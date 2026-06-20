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


class AdzunaScraper:
    BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

    def __init__(self, app_id: str, api_key: str, country: str = "us"):
        self.app_id = app_id
        self.api_key = api_key
        self.country = country

    MAX_PAGE = 50  # Adzuna free tier hard limit

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
    def fetch_batch(self, query: str, location: str = "", page: int = 1, results_per_page: int = 50) -> list[dict]:
        if page > self.MAX_PAGE:
            return []

        url = self.BASE_URL.format(country=self.country, page=page)
        # NOTE: Adzuna's API requires app_id and app_key as URL query parameters.
        # This is the vendor's auth design and cannot be changed on our side.
        # See: https://developer.adzuna.com/activedocs
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": results_per_page,
            "what": query,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 400:
            return []  # pagination limit reached, not a retriable error
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])

    def scrape_all(
        self,
        job_titles: list[str],
        locations: list[str],
        max_jobs: int = 10000,
        output_dir: str = "data/raw",
    ) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"adzuna_{timestamp}.jsonl"

        total = 0
        with open(out_path, "w") as f:
            outer = tqdm(job_titles, desc="Job titles")
            for title in outer:
                for location in locations:
                    page = 1
                    while total < max_jobs:
                        try:
                            batch = self.fetch_batch(title, location, page)
                        except Exception as e:
                            logger.error("Error fetching %s/%s page %d: %s", title, location, page, e)
                            break
                        if not batch:
                            break
                        for job in batch:
                            job["_query"] = title
                            job["_location_query"] = location
                            job["_scraped_at"] = datetime.utcnow().isoformat()
                            f.write(json.dumps(job) + "\n")
                            total += 1
                        outer.set_postfix(total=total)
                        page += 1
                        time.sleep(1.0)  # respect rate limit
                        if len(batch) < 50:
                            break

        logger.info("Saved %d jobs to %s", total, out_path)
        return out_path
