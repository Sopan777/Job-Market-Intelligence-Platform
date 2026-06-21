import re
import json
import warnings
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from src.logger import get_logger

logger = get_logger(__name__)

_BOILERPLATE = re.compile(
    r"equal opportunity employer|eoe|e\.o\.e\.|affirmative action|"
    r"we are an equal|disability|veteran status|background check|"
    r"authorized to work in the",
    re.IGNORECASE,
)


def clean_description(text: str) -> str:
    if not text:
        return ""
    # Strip HTML
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove boilerplate sentences
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if not _BOILERPLATE.search(s)]
    return " ".join(sentences)


def build_master_df(raw_dir: str = "data/raw") -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    records = []

    for jsonl_file in sorted(raw_dir.glob("*.jsonl")):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    job = json.loads(line)
                    records.append({
                        "id": job.get("id", ""),
                        "title": job.get("title", ""),
                        "company": _extract_company(job),
                        "location": _extract_location(job),
                        "description_raw": job.get("description", ""),
                        "created": job.get("created", ""),
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "source": job.get("_source", "unknown"),
                        "query": job.get("_query", ""),
                        "scraped_at": job.get("_scraped_at", ""),
                    })
                except json.JSONDecodeError:
                    continue

    if not records:
        raise ValueError(f"No .jsonl files found in {raw_dir}")

    df = pd.DataFrame(records)

    # Clean descriptions
    df["description"] = df["description_raw"].apply(clean_description)

    # Parse dates — suppress UserWarning about timezone info being dropped
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        df["date"] = pd.to_datetime(df["created"], utc=True, errors="coerce")
        df["week"] = df["date"].dt.to_period("W").dt.start_time

    # Deduplicate by title + company + date (same posting across queries)
    df = df.drop_duplicates(subset=["title", "company", "created"]).reset_index(drop=True)

    return df


def save_clean(df: pd.DataFrame, output_path: str = "data/processed/jobs_clean.parquet") -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.info("Saved %d clean jobs to %s", len(df), out)
    return out


def _extract_company(job: dict) -> str:
    company = job.get("company", {})
    if isinstance(company, dict):
        return company.get("display_name", "")
    return str(company)


def _extract_location(job: dict) -> str:
    location = job.get("location", {})
    if isinstance(location, dict):
        return location.get("display_name", "")
    return str(location)
