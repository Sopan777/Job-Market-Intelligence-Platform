from datetime import datetime, timedelta

import pandas as pd
import pytest
import spacy

from src.nlp.extractor import build_matcher, load_skills_vocabulary
from src.analyzer.gap import (
    GapReport,
    classify_demand,
    compute_market_percentile,
    compute_readiness_score,
    get_emerging_skills,
    get_role_top_skills,
    get_skill_frequencies,
    get_skill_weights,
    resolve_role_subset,
    analyse_gap,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nlp_resources():
    nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
    skills = load_skills_vocabulary()
    matcher = build_matcher(skills, nlp)
    skill_lookup = {s.lower(): s for s in skills}
    return nlp, matcher, skill_lookup


def _make_jobs_df() -> pd.DataFrame:
    base = datetime(2024, 1, 1)
    records = []
    clusters = {
        "Machine / Learning": ["python", "tensorflow", "pytorch", "scikit-learn", "mlflow", "docker"],
        "Data / Scientist":   ["python", "sql", "statistics", "pandas", "numpy", "r"],
        "Software / Developer": ["java", "go", "kubernetes", "docker", "rest api", "git"],
    }
    for cluster, skills in clusters.items():
        for i in range(20):
            records.append({
                "id": f"{cluster}_{i}",
                "title": cluster.replace(" / ", " ").lower(),
                "company": "Acme",
                "location": "Remote",
                "description": " ".join(skills),
                "date": base + timedelta(days=i),
                "week": base,
                "source": "mock",
                "query": cluster,
                "skills": skills,
                "skill_count": len(skills),
                "cluster": list(clusters.keys()).index(cluster),
                "cluster_name": cluster,
            })
    return pd.DataFrame(records)


def _make_forecasts_df() -> pd.DataFrame:
    base = datetime(2024, 1, 1)
    records = []
    skill_slopes = {"python": 0.5, "docker": 0.3, "tensorflow": 0.15, "sql": -0.2, "java": 0.05}
    for skill, slope in skill_slopes.items():
        for i in range(10):
            records.append({
                "skill": skill,
                "ds": base + timedelta(weeks=i),
                "yhat": 10 + i,
                "yhat_lower": 8 + i,
                "yhat_upper": 12 + i,
                "trend_slope": slope,
                "y": 10 + i,
            })
    return pd.DataFrame(records)


# ── resolve_role_subset ───────────────────────────────────────────────────────

def test_resolve_role_subset_uses_cluster_name():
    df = _make_jobs_df()
    resume_skills = ["python", "tensorflow", "pytorch", "scikit-learn"]
    subset = resolve_role_subset(df, "ML Engineer", resume_skills)
    assert subset["cluster_name"].unique().tolist() == ["Machine / Learning"]


def test_resolve_role_subset_falls_back_to_title():
    df = _make_jobs_df().drop(columns=["cluster_name"])
    resume_skills = ["python", "sql"]
    subset = resolve_role_subset(df, "Data Scientist", resume_skills)
    # fallback uses title keyword matching — should narrow the df
    assert len(subset) < len(df)


def test_resolve_role_subset_fallback_when_no_match():
    df = _make_jobs_df().drop(columns=["cluster_name", "title"])
    resume_skills = ["cobol"]
    subset = resolve_role_subset(df, "ML Engineer", resume_skills)
    assert len(subset) == len(df)


# ── get_skill_frequencies / get_skill_weights ─────────────────────────────────

def test_get_skill_frequencies_ordering():
    df = _make_jobs_df()
    ml_df = df[df["cluster_name"] == "Machine / Learning"]
    freq = get_skill_frequencies(ml_df)
    assert freq.index[0] == "python"  # python appears in every row


def test_get_skill_weights_sum_to_one():
    df = _make_jobs_df()
    freq = get_skill_frequencies(df)
    weights = get_skill_weights(freq)
    assert abs(weights.sum() - 1.0) < 1e-6


def test_get_skill_weights_empty_series():
    weights = get_skill_weights(pd.Series(dtype=int))
    assert weights.empty


# ── get_role_top_skills ───────────────────────────────────────────────────────

def test_get_role_top_skills_ordering():
    df = _make_jobs_df()
    skills = get_role_top_skills(df)
    freq = get_skill_frequencies(df)
    assert skills[0] == freq.index[0]


def test_get_role_top_skills_respects_top_n():
    df = _make_jobs_df()
    skills = get_role_top_skills(df, top_n=3)
    assert len(skills) <= 3


# ── classify_demand ───────────────────────────────────────────────────────────

def test_classify_demand_high():
    freq = pd.Series({"python": 100, "sql": 50, "docker": 10})
    assert classify_demand("python", freq) == "High"


def test_classify_demand_medium():
    freq = pd.Series({"python": 100, "sql": 20, "docker": 5})
    assert classify_demand("sql", freq) == "Medium"


def test_classify_demand_low():
    freq = pd.Series({"python": 100, "sql": 50, "docker": 5})
    assert classify_demand("docker", freq) == "Low"


def test_classify_demand_unknown_skill():
    freq = pd.Series({"python": 100})
    assert classify_demand("cobol", freq) == "Low"


def test_classify_demand_empty_series():
    assert classify_demand("python", pd.Series(dtype=int)) == "Low"


# ── get_emerging_skills ───────────────────────────────────────────────────────

def test_get_emerging_skills_uses_resume_skills():
    forecasts = _make_forecasts_df()
    # python (slope=0.5) and docker (slope=0.3) are on resume and above threshold
    result = get_emerging_skills(["python", "docker", "sql"], forecasts)
    assert "python" in result
    assert "docker" in result
    # sql has slope=-0.2, should not appear
    assert "sql" not in result


def test_get_emerging_skills_filters_by_slope():
    forecasts = _make_forecasts_df()
    # java has slope=0.05, below default threshold 0.1
    result = get_emerging_skills(["java"], forecasts)
    assert "java" not in result


def test_get_emerging_skills_empty_forecasts():
    result = get_emerging_skills(["python"], pd.DataFrame())
    assert result == []


def test_get_emerging_skills_missing_column():
    df = pd.DataFrame({"skill": ["python"], "yhat": [10]})
    result = get_emerging_skills(["python"], df)
    assert result == []


def test_get_emerging_skills_sorted_by_slope():
    forecasts = _make_forecasts_df()
    result = get_emerging_skills(["python", "docker", "tensorflow"], forecasts)
    # python (0.5) > docker (0.3) > tensorflow (0.15)
    assert result.index("python") < result.index("docker")


# ── compute_readiness_score ───────────────────────────────────────────────────

def test_compute_readiness_score_full_overlap():
    role_skills = ["python", "sql", "docker"]
    weights = pd.Series({"python": 0.5, "sql": 0.3, "docker": 0.2})
    score = compute_readiness_score(role_skills, role_skills, weights)
    assert score == 100


def test_compute_readiness_score_no_overlap():
    resume = ["cobol", "fortran"]
    role_skills = ["python", "sql", "docker"]
    weights = pd.Series({"python": 0.5, "sql": 0.3, "docker": 0.2})
    assert compute_readiness_score(resume, role_skills, weights) == 0


def test_compute_readiness_score_weighted_vs_uniform():
    # Matching only the high-weight skill should give higher score than matching only low-weight
    role_skills = ["python", "docker"]
    weights = pd.Series({"python": 0.9, "docker": 0.1})
    score_high = compute_readiness_score(["python"], role_skills, weights)
    score_low = compute_readiness_score(["docker"], role_skills, weights)
    assert score_high > score_low


def test_compute_readiness_score_case_insensitive():
    role_skills = ["python", "sql"]
    weights = pd.Series({"python": 0.6, "sql": 0.4})
    score = compute_readiness_score(["Python", "SQL"], role_skills, weights)
    assert score == 100


def test_compute_readiness_score_empty_role_skills():
    assert compute_readiness_score(["python"], [], pd.Series(dtype=float)) == 0


# ── compute_market_percentile ─────────────────────────────────────────────────

def test_compute_market_percentile_returns_int():
    df = _make_jobs_df()
    ml_df = df[df["cluster_name"] == "Machine / Learning"]
    freq = get_skill_frequencies(ml_df)
    weights = get_skill_weights(freq)
    role_skills = get_role_top_skills(ml_df, top_n=10)
    pct = compute_market_percentile(50, ml_df, role_skills, weights)
    assert pct is None or (0 <= pct <= 100)


def test_compute_market_percentile_too_few_jobs():
    df = _make_jobs_df().head(5)
    freq = get_skill_frequencies(df)
    weights = get_skill_weights(freq)
    role_skills = get_role_top_skills(df)
    result = compute_market_percentile(50, df, role_skills, weights)
    assert result is None


# ── analyse_gap integration ───────────────────────────────────────────────────

def test_analyse_gap_integration(nlp_resources):
    nlp, matcher, skill_lookup = nlp_resources
    df = _make_jobs_df()
    forecasts = _make_forecasts_df()
    resume = "Experienced ML engineer with Python, TensorFlow, PyTorch, and Docker experience."
    report = analyse_gap(resume, "ML Engineer", df, forecasts, nlp, matcher, skill_lookup)
    assert isinstance(report, GapReport)
    assert 0 <= report.readiness_score <= 100
    assert report.jobs_analysed > 0
    assert isinstance(report.resume_skills, list)
    assert isinstance(report.skills_present, list)
    assert isinstance(report.skills_missing, list)


def test_analyse_gap_empty_resume(nlp_resources):
    nlp, matcher, skill_lookup = nlp_resources
    df = _make_jobs_df()
    report = analyse_gap("", "Data Scientist", df, pd.DataFrame(), nlp, matcher, skill_lookup)
    assert report.readiness_score == 0
    assert report.resume_skills == []
    assert isinstance(report.skills_missing, list)
