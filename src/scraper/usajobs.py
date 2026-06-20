import time
import json
import os
from pathlib import Path
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from src.logger import get_logger

logger = get_logger(__name__)


class USAJobsScraper:
    """
    Scrapes USAJobs.gov — free, no auth required, public domain data.
    https://developer.usajobs.gov/
    """
    BASE_URL = "https://data.usajobs.gov/api/search"
    HEADERS = {
        "Host": "data.usajobs.gov",
        "User-Agent": "job-market-intelligence/1.0",
        # Set USAJOBS_API_KEY env var for higher rate limits; empty string = anonymous access.
        "Authorization-Key": os.environ.get("USAJOBS_API_KEY", ""),
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_batch(self, keyword: str, page: int = 1, results_per_page: int = 50) -> list[dict]:
        params = {
            "Keyword": keyword,
            "ResultsPerPage": results_per_page,
            "Page": page,
        }
        resp = requests.get(self.BASE_URL, headers=self.HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("SearchResult", {}).get("SearchResultItems", [])
        return [item.get("MatchedObjectDescriptor", {}) for item in items]

    def scrape_all(
        self,
        keywords: list[str],
        max_jobs: int = 5000,
        output_dir: str = "data/raw",
    ) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"usajobs_{timestamp}.jsonl"

        total = 0
        with open(out_path, "w") as f:
            for keyword in tqdm(keywords, desc="USAJobs keywords"):
                page = 1
                while total < max_jobs:
                    try:
                        batch = self.fetch_batch(keyword, page)
                    except Exception as e:
                        logger.error("Error fetching '%s' page %d: %s", keyword, page, e)
                        break
                    if not batch:
                        break
                    for job in batch:
                        normalized = _normalize_usajobs(job, keyword)
                        f.write(json.dumps(normalized) + "\n")
                        total += 1
                    page += 1
                    time.sleep(0.5)
                    if len(batch) < 50:
                        break

        logger.info("Saved %d USAJobs records to %s", total, out_path)
        return out_path


def _normalize_usajobs(job: dict, query: str) -> dict:
    """Map USAJobs fields to the same schema as Adzuna."""
    return {
        "id": job.get("PositionID", ""),
        "title": job.get("PositionTitle", ""),
        "company": {"display_name": job.get("OrganizationName", "")},
        "location": {"display_name": job.get("PositionLocationDisplay", "")},
        "description": job.get("UserArea", {}).get("Details", {}).get("JobSummary", ""),
        "created": job.get("PublicationStartDate", ""),
        "salary_min": None,
        "salary_max": None,
        "_query": query,
        "_source": "usajobs",
        "_scraped_at": datetime.utcnow().isoformat(),
    }
