from fastapi import APIRouter
from api.data import load_jobs

router = APIRouter()


@router.get("/overview")
def overview():
    df = load_jobs()
    if df.empty:
        return {"empty": True, "total_jobs": 0, "unique_skills": 0, "n_clusters": 0, "n_sources": 0, "top_skills": [], "weekly_postings": []}

    all_skills = df["skills"].explode() if "skills" in df.columns else None
    unique_skills = int(all_skills.dropna().nunique()) if all_skills is not None else 0
    n_clusters = int(df["cluster"].nunique()) if "cluster" in df.columns else 0
    n_sources = int(df["source"].nunique()) if "source" in df.columns else 0

    top_skills = []
    if all_skills is not None and not all_skills.dropna().empty:
        counts = all_skills.value_counts().head(30)
        top_skills = [{"skill": k, "count": int(v)} for k, v in counts.items()]

    weekly_postings = []
    if "week" in df.columns:
        import pandas as pd
        weekly = df.groupby("week").size().reset_index(name="count")
        weekly["week"] = pd.to_datetime(weekly["week"])
        weekly_postings = [
            {"week": row["week"].isoformat(), "count": int(row["count"])}
            for _, row in weekly.iterrows()
        ]

    return {
        "empty": False,
        "total_jobs": len(df),
        "unique_skills": unique_skills,
        "n_clusters": n_clusters,
        "n_sources": n_sources,
        "top_skills": top_skills,
        "weekly_postings": weekly_postings,
    }
