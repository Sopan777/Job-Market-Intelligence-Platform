from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.nlp.extractor import extract_skills
from src.logger import get_logger

logger = get_logger(__name__)

EMERGING_SLOPE_THRESHOLD: float = 0.1
TOP_N_ROLE_SKILLS: int = 20

# Fallback keyword map used only when cluster_name is absent
_FALLBACK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ML Engineer":       ("machine learning", "ml engineer", "mlops", "ai engineer"),
    "Data Scientist":    ("data scientist", "data science", "research scientist"),
    "Data Analyst":      ("data analyst", "business analyst", "analytics", "bi analyst"),
    "Software Engineer": ("software engineer", "backend engineer", "frontend engineer",
                          "fullstack", "developer", "swe"),
}

ROLE_KEYWORDS = _FALLBACK_KEYWORDS  # exported for dashboard selectbox


@dataclass
class GapReport:
    role: str
    resume_skills: list[str]
    role_top_skills: list[str]
    skills_present: list[str]
    skills_missing: list[str]
    emerging_skills: list[str]
    readiness_score: int
    skill_demand: dict[str, str]
    skill_weights: dict[str, float]
    jobs_analysed: int
    market_percentile: int | None = field(default=None)


def resolve_role_subset(
    df: pd.DataFrame,
    role: str,
    resume_skills: list[str],
) -> pd.DataFrame:
    resume_set = {s.lower() for s in resume_skills}

    if "cluster_name" in df.columns and "skills" in df.columns:
        clusters = [c for c in df["cluster_name"].unique() if c and c != "Uncategorized"]
        if clusters:
            best_cluster, best_overlap = None, -1
            for cluster in clusters:
                cluster_skills = (
                    df[df["cluster_name"] == cluster]["skills"]
                    .explode()
                    .dropna()
                    .str.lower()
                    .value_counts()
                    .head(TOP_N_ROLE_SKILLS)
                    .index
                )
                overlap = len(resume_set & set(cluster_skills))
                if overlap > best_overlap:
                    best_overlap, best_cluster = overlap, cluster
            if best_cluster is not None and best_overlap >= 0:
                subset = df[df["cluster_name"] == best_cluster]
                if not subset.empty:
                    return subset

    # Fallback: title keyword scoring
    keywords = _FALLBACK_KEYWORDS.get(role, ())
    if keywords and "title" in df.columns:
        titles_lower = df["title"].str.lower().fillna("")
        scores = sum(titles_lower.str.contains(kw, regex=False).astype(int) for kw in keywords)
        max_score = scores.max()
        if max_score > 0:
            return df[scores == max_score]

    logger.warning("resolve_role_subset: no cluster or title match for role=%r; returning full df (%d rows)", role, len(df))
    return df


def get_skill_frequencies(role_df: pd.DataFrame) -> pd.Series:
    if "skills" not in role_df.columns:
        return pd.Series(dtype=int)
    return (
        role_df["skills"]
        .explode()
        .dropna()
        .str.lower()
        .value_counts()
    )


def get_skill_weights(skill_freq: pd.Series) -> pd.Series:
    total = skill_freq.sum()
    if total == 0:
        return skill_freq.astype(float)
    return skill_freq / total


def get_role_top_skills(role_df: pd.DataFrame, top_n: int = TOP_N_ROLE_SKILLS) -> list[str]:
    return get_skill_frequencies(role_df).head(top_n).index.tolist()


def classify_demand(skill: str, skill_freq: pd.Series) -> str:
    if skill_freq.empty or skill not in skill_freq.index:
        return "Low"
    max_freq = skill_freq.max()
    if max_freq == 0:
        return "Low"
    freq = skill_freq[skill]
    if freq >= 0.33 * max_freq:
        return "High"
    if freq >= 0.10 * max_freq:
        return "Medium"
    return "Low"


def get_emerging_skills(
    resume_skills: list[str],
    forecasts: pd.DataFrame,
    threshold: float = EMERGING_SLOPE_THRESHOLD,
) -> list[str]:
    if forecasts.empty or "trend_slope" not in forecasts.columns or "skill" not in forecasts.columns:
        return []

    resume_lower = {s.lower() for s in resume_skills}
    slopes = (
        forecasts.groupby("skill")["trend_slope"]
        .first()
        .reset_index()
    )
    emerging = slopes[
        (slopes["trend_slope"] > threshold) &
        (slopes["skill"].str.lower().isin(resume_lower))
    ].sort_values("trend_slope", ascending=False)

    return emerging["skill"].tolist()


def compute_readiness_score(
    resume_skills: list[str],
    role_top_skills: list[str],
    skill_weights: pd.Series,
) -> int:
    if not role_top_skills:
        return 0

    resume_lower = {s.lower() for s in resume_skills}
    role_lower = [s.lower() for s in role_top_skills]

    matched_weight = sum(
        skill_weights.get(s, 0.0) for s in role_lower if s in resume_lower
    )
    total_weight = sum(skill_weights.get(s, 0.0) for s in role_lower)

    if total_weight == 0:
        # Fallback to unweighted if weights are all zero
        matched = sum(1 for s in role_lower if s in resume_lower)
        return round(100 * matched / len(role_lower))

    return min(100, round(100 * matched_weight / total_weight))


def compute_market_percentile(
    score: int,
    role_df: pd.DataFrame,
    role_top_skills: list[str],
    skill_weights: pd.Series,
) -> int | None:
    if "skills" not in role_df.columns or len(role_df) < 10:
        return None

    job_scores = role_df["skills"].apply(
        lambda skills: compute_readiness_score(
            skills if isinstance(skills, list) else [],
            role_top_skills,
            skill_weights,
        )
    )
    below = (job_scores < score).sum()
    return round(100 * below / len(job_scores))


def analyse_gap(
    resume_text: str,
    role: str,
    df: pd.DataFrame,
    forecasts: pd.DataFrame,
    nlp,
    matcher,
    skill_lookup: dict[str, str],
    top_n: int = TOP_N_ROLE_SKILLS,
) -> GapReport:
    resume_skills = extract_skills(resume_text, matcher, nlp, skill_lookup)

    role_df = resolve_role_subset(df, role, resume_skills)
    if role_df.empty:
        logger.warning("analyse_gap: role_df is empty for role=%r", role)

    skill_freq = get_skill_frequencies(role_df)
    skill_weights_series = get_skill_weights(skill_freq)
    role_top_skills = get_role_top_skills(role_df, top_n)

    resume_lower = {s.lower() for s in resume_skills}
    role_top_lower = [s.lower() for s in role_top_skills]

    skills_present = [s for s in role_top_lower if s in resume_lower]
    skills_missing = [s for s in role_top_lower if s not in resume_lower]

    emerging_skills = get_emerging_skills(resume_skills, forecasts)

    score = compute_readiness_score(resume_skills, role_top_skills, skill_weights_series)
    percentile = compute_market_percentile(score, role_df, role_top_skills, skill_weights_series)

    skill_demand = {s: classify_demand(s, skill_freq) for s in role_top_lower}
    skill_weights_dict = {s: float(skill_weights_series.get(s, 0.0)) for s in role_top_lower}

    return GapReport(
        role=role,
        resume_skills=resume_skills,
        role_top_skills=role_top_skills,
        skills_present=skills_present,
        skills_missing=skills_missing,
        emerging_skills=emerging_skills,
        readiness_score=score,
        skill_demand=skill_demand,
        skill_weights=skill_weights_dict,
        jobs_analysed=len(role_df),
        market_percentile=percentile,
    )
