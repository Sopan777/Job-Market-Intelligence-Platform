from fastapi import APIRouter, Query
from typing import List
from api.data import load_jobs

router = APIRouter()


@router.get("/heatmap")
def heatmap(clusters: List[str] = Query(default=[])):
    df = load_jobs()
    if df.empty or "cluster_name" not in df.columns or "skills" not in df.columns:
        return {"empty": True, "clusters": [], "skills": [], "values": []}

    top_skills = df["skills"].explode().value_counts().head(25).index.tolist()
    all_clusters = [c for c in df["cluster_name"].unique() if c != "Uncategorized"]

    selected = clusters if clusters else all_clusters[:10]

    heat_df = df[df["cluster_name"].isin(selected)].copy()
    heat_df = heat_df.explode("skills")
    heat_df = heat_df[heat_df["skills"].isin(top_skills)]

    pivot = (
        heat_df.groupby(["cluster_name", "skills"])
        .size()
        .reset_index(name="count")
        .pivot(index="cluster_name", columns="skills", values="count")
        .fillna(0)
    )

    if pivot.empty:
        return {"empty": True, "clusters": [], "skills": [], "values": []}

    return {
        "empty": False,
        "all_clusters": all_clusters,
        "clusters": pivot.index.tolist(),
        "skills": pivot.columns.tolist(),
        "values": pivot.values.tolist(),
    }
