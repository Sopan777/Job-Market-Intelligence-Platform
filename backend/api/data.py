from functools import lru_cache
from pathlib import Path
import os
import pandas as pd

# Allow override via env var; default resolves to <repo-root>/data/processed
# regardless of whether uvicorn runs from backend/ or repo root
_here = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = Path(os.environ.get("DATA_DIR", str(_here.parent / "data" / "processed")))


@lru_cache(maxsize=1)
def load_jobs() -> pd.DataFrame:
    clustered = DATA_DIR / "jobs_clustered.parquet"
    skills_file = DATA_DIR / "jobs_with_skills.parquet"
    if clustered.exists():
        return pd.read_parquet(clustered)
    if skills_file.exists():
        return pd.read_parquet(skills_file)
    return pd.DataFrame()


@lru_cache(maxsize=1)
def load_forecasts() -> pd.DataFrame:
    f = DATA_DIR / "forecasts.parquet"
    if f.exists():
        return pd.read_parquet(f)
    return pd.DataFrame()


def nlp_components():
    try:
        import spacy
        from src.nlp.extractor import build_matcher, load_skills_vocabulary
        nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        skills = load_skills_vocabulary()
        matcher = build_matcher(skills, nlp)
        skill_lookup = {s.lower(): s for s in skills}
        return nlp, matcher, skill_lookup
    except Exception:
        return None, None, None


_nlp, _matcher, _skill_lookup = None, None, None
_nlp_loaded = False


def get_nlp():
    global _nlp, _matcher, _skill_lookup, _nlp_loaded
    if not _nlp_loaded:
        _nlp, _matcher, _skill_lookup = nlp_components()
        _nlp_loaded = True
    return _nlp, _matcher, _skill_lookup
