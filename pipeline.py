#!/usr/bin/env python3
"""
Job Market Intelligence Platform — Pipeline CLI
Usage:
    python pipeline.py --all                 # full pipeline with mock data
    python pipeline.py --scrape --max-jobs 500
    python pipeline.py --clean
    python pipeline.py --extract
    python pipeline.py --cluster
    python pipeline.py --forecast
    streamlit run src/dashboard/app.py
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")


def run_scrape(max_jobs: int, use_mock: bool) -> None:
    app_id = os.getenv("ADZUNA_APP_ID", "")
    api_key = os.getenv("ADZUNA_API_KEY", "")

    if use_mock or not (app_id and api_key) or "your_" in app_id:
        print("No Adzuna credentials found — generating mock data.")
        from src.scraper.mock import generate_mock_jobs
        generate_mock_jobs(n=max_jobs, output_dir=str(DATA_RAW))
    else:
        from src.scraper.adzuna import AdzunaScraper
        scraper = AdzunaScraper(app_id, api_key)
        job_titles = [
            "data scientist", "software engineer", "data engineer",
            "machine learning engineer", "frontend engineer", "devops engineer",
            "product manager", "backend engineer",
        ]
        locations = ["", "New York", "San Francisco", "Seattle", "Remote"]
        scraper.scrape_all(job_titles, locations, max_jobs=max_jobs, output_dir=str(DATA_RAW))

        # Supplement with USAJobs (free, no key)
        print("\nFetching USAJobs data...")
        from src.scraper.usajobs import USAJobsScraper
        usa = USAJobsScraper()
        usa.scrape_all(
            keywords=["data scientist", "software developer", "machine learning"],
            max_jobs=min(2000, max_jobs // 5),
            output_dir=str(DATA_RAW),
        )


def run_clean() -> None:
    from src.nlp.cleaner import build_master_df, save_clean
    print("Building master DataFrame from raw data...")
    df = build_master_df(str(DATA_RAW))
    print(f"  {len(df)} unique jobs after deduplication")
    save_clean(df)


def run_extract() -> None:
    import pandas as pd
    from src.nlp.extractor import add_skills_column

    clean_path = DATA_PROCESSED / "jobs_clean.parquet"
    if not clean_path.exists():
        print("jobs_clean.parquet not found — run --clean first.")
        sys.exit(1)

    df = pd.read_parquet(clean_path)
    print(f"Extracting skills from {len(df)} jobs...")
    add_skills_column(df, output_path=str(DATA_PROCESSED / "jobs_with_skills.parquet"))


def run_cluster() -> None:
    import pandas as pd
    from src.clustering.roles import run_clustering

    skills_path = DATA_PROCESSED / "jobs_with_skills.parquet"
    if not skills_path.exists():
        print("jobs_with_skills.parquet not found — run --extract first.")
        sys.exit(1)

    df = pd.read_parquet(skills_path)
    print(f"Clustering {len(df)} jobs...")
    run_clustering(df, output_path=str(DATA_PROCESSED / "jobs_clustered.parquet"))


def run_forecast() -> None:
    import pandas as pd
    from src.forecasting.demand import forecast_all_skills

    # Use clustered if available, fall back to skills
    for fname in ("jobs_clustered.parquet", "jobs_with_skills.parquet"):
        p = DATA_PROCESSED / fname
        if p.exists():
            df = pd.read_parquet(p)
            break
    else:
        print("No processed data found — run --extract first.")
        sys.exit(1)

    print(f"Forecasting skill demand from {len(df)} jobs...")
    forecast_all_skills(df, top_n=50, output_path=str(DATA_PROCESSED / "forecasts.parquet"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Market Intelligence Pipeline")
    parser.add_argument("--scrape", action="store_true", help="Scrape job postings")
    parser.add_argument("--clean", action="store_true", help="Clean raw data")
    parser.add_argument("--extract", action="store_true", help="Extract skills via NLP")
    parser.add_argument("--cluster", action="store_true", help="Cluster job roles")
    parser.add_argument("--forecast", action="store_true", help="Forecast skill demand")
    parser.add_argument("--all", dest="run_all", action="store_true", help="Run full pipeline")
    parser.add_argument("--max-jobs", type=int, default=500, help="Max jobs to scrape (default 500)")
    parser.add_argument("--mock", action="store_true", help="Force mock data even if API keys set")
    args = parser.parse_args()

    if not any([args.scrape, args.clean, args.extract, args.cluster, args.forecast, args.run_all]):
        parser.print_help()
        sys.exit(0)

    steps = []
    if args.run_all:
        steps = ["scrape", "clean", "extract", "cluster", "forecast"]
    else:
        if args.scrape:
            steps.append("scrape")
        if args.clean:
            steps.append("clean")
        if args.extract:
            steps.append("extract")
        if args.cluster:
            steps.append("cluster")
        if args.forecast:
            steps.append("forecast")

    for step in steps:
        print(f"\n{'='*50}\nSTEP: {step.upper()}\n{'='*50}")
        if step == "scrape":
            run_scrape(args.max_jobs, args.mock)
        elif step == "clean":
            run_clean()
        elif step == "extract":
            run_extract()
        elif step == "cluster":
            run_cluster()
        elif step == "forecast":
            run_forecast()

    print("\nPipeline complete.")
    if "forecast" in steps:
        print("Launch dashboard:  streamlit run src/dashboard/app.py")


if __name__ == "__main__":
    main()
