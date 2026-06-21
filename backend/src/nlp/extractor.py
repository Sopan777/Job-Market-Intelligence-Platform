"""
Skill extraction using a curated skills vocabulary matched via spaCy PhraseMatcher.
Falls back to a bundled ~300-skill list if the ESCO CSV is not available.
"""
import re
import csv
from pathlib import Path
from typing import Optional

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from tqdm import tqdm

from src.logger import get_logger

logger = get_logger(__name__)


# Bundled fallback skill list (covers the most common tech/data/PM skills)
FALLBACK_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#", "R", "Scala",
    "SQL", "NoSQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "AWS", "GCP", "Azure", "Kubernetes", "Docker", "Terraform", "Ansible", "Helm",
    "React", "Next.js", "Vue.js", "Angular", "Node.js", "FastAPI", "Django", "Flask",
    "machine learning", "deep learning", "NLP", "computer vision", "reinforcement learning",
    "TensorFlow", "PyTorch", "scikit-learn", "Keras", "JAX", "XGBoost", "LightGBM",
    "pandas", "NumPy", "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Snowflake",
    "BigQuery", "Redshift", "data warehouse", "data lake", "ETL", "feature engineering",
    "MLflow", "Kubeflow", "SageMaker", "Vertex AI", "model serving", "ONNX",
    "Git", "CI/CD", "GitHub Actions", "Jenkins", "CircleCI", "Datadog", "Grafana",
    "Prometheus", "Terraform", "Linux", "bash", "REST API", "GraphQL", "gRPC",
    "microservices", "distributed systems", "system design", "A/B testing",
    "statistics", "probability", "data visualization", "Tableau", "Power BI", "Looker",
    "Jupyter", "VS Code", "Jira", "Confluence", "agile", "scrum", "roadmap planning",
    "stakeholder management", "user research", "product management", "OKRs",
    "communication", "leadership", "mentoring", "problem solving", "critical thinking",
]


def load_skills_vocabulary(skills_path: Optional[str] = None) -> list[str]:
    if skills_path:
        p = Path(skills_path)
        if p.exists():
            skills = []
            with open(p, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    label = row.get("preferredLabel") or row.get("skill") or ""
                    if label:
                        skills.append(label.strip())
            if skills:
                logger.info("Loaded %d skills from %s", len(skills), p)
                return skills

    logger.info("Using bundled skill vocabulary (%d skills)", len(FALLBACK_SKILLS))
    return FALLBACK_SKILLS


def build_matcher(skills: list[str], nlp) -> PhraseMatcher:
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(s.lower()) for s in skills]
    matcher.add("SKILLS", patterns)
    return matcher


def extract_skills(text: str, matcher: PhraseMatcher, nlp, skill_lookup: dict[str, str]) -> list[str]:
    """
    Extract skills from text using PhraseMatcher.
    skill_lookup maps lowercase skill → original-cased skill for display.
    """
    if not text:
        return []
    doc = nlp(text.lower()[:15000])  # increased from 5000 to capture full descriptions
    matches = matcher(doc)
    found = set()
    for _, start, end in matches:
        span_text = doc[start:end].text  # lowercased (doc is lowercased)
        # Restore original casing via lookup; fall back to span_text if not found
        found.add(skill_lookup.get(span_text, span_text))
    return sorted(found)


def add_skills_column(
    df: pd.DataFrame,
    skills_path: Optional[str] = None,
    output_path: str = "data/processed/jobs_with_skills.parquet",
) -> pd.DataFrame:
    nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
    skills = load_skills_vocabulary(skills_path)
    # dict mapping lowercase → original case for display normalisation
    skill_lookup = {s.lower(): s for s in skills}
    matcher = build_matcher(skills, nlp)

    tqdm.pandas(desc="Extracting skills")
    df["skills"] = df["description"].progress_apply(
        lambda t: extract_skills(t, matcher, nlp, skill_lookup)
    )
    df["skill_count"] = df["skills"].apply(len)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.info("Saved %d rows with skills to %s", len(df), out)
    return df
