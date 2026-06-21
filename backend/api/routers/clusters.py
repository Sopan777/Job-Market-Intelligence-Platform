from fastapi import APIRouter
from api.data import load_jobs

router = APIRouter()


@router.get("/clusters")
def clusters():
    df = load_jobs()
    if df.empty or "umap_x" not in df.columns:
        return {"empty": True, "points": [], "cluster_sizes": []}

    plot_df = df[df["cluster"] != -1].copy() if "cluster" in df.columns else df.copy()
    sample = plot_df.sample(min(5000, len(plot_df)), random_state=42)

    points = []
    for _, row in sample.iterrows():
        points.append({
            "umap_x": float(row["umap_x"]),
            "umap_y": float(row["umap_y"]),
            "cluster_name": str(row.get("cluster_name", "")),
            "title": str(row.get("title", "")),
            "company": str(row.get("company", "")),
            "location": str(row.get("location", "")),
        })

    if "cluster" in df.columns:
        sizes_series = df[df["cluster"] != -1]["cluster_name"].value_counts()
    else:
        sizes_series = df["cluster_name"].value_counts()

    cluster_sizes = [{"cluster": k, "count": int(v)} for k, v in sizes_series.items()]

    return {"empty": False, "points": points, "cluster_sizes": cluster_sizes}
