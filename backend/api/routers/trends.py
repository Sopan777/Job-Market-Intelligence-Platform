from fastapi import APIRouter
from api.data import load_forecasts

router = APIRouter()


@router.get("/trends")
def trends():
    fc = load_forecasts()
    if fc.empty:
        return {"empty": True, "skills": [], "rising": [], "falling": [], "data": []}

    available_skills = sorted(fc["skill"].unique().tolist())

    rising, falling = [], []
    if "trend_slope" in fc.columns:
        summary = fc.groupby("skill")["trend_slope"].first().reset_index()
        rising = summary[summary["trend_slope"] > 0.1]["skill"].tolist()
        falling = summary[summary["trend_slope"] < -0.1]["skill"].tolist()

    data = []
    for _, row in fc.iterrows():
        entry = {
            "skill": str(row["skill"]),
            "ds": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
            "y": float(row["y"]) if "y" in fc.columns and row["y"] == row["y"] else None,
            "yhat": float(row["yhat"]) if row["yhat"] == row["yhat"] else None,
            "yhat_lower": float(row["yhat_lower"]) if "yhat_lower" in fc.columns and row["yhat_lower"] == row["yhat_lower"] else None,
            "yhat_upper": float(row["yhat_upper"]) if "yhat_upper" in fc.columns and row["yhat_upper"] == row["yhat_upper"] else None,
        }
        data.append(entry)

    return {
        "empty": False,
        "skills": available_skills,
        "rising": rising,
        "falling": falling,
        "data": data,
    }
