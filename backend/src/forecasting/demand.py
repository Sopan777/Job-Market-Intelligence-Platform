"""
Skill demand forecasting using Holt-Winters exponential smoothing (statsmodels).
Builds weekly time-series per skill → fits additive-trend model → projects 26 weeks forward.
Output schema is identical to the former Prophet-based version so the dashboard is unchanged.
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.logger import get_logger

logger = get_logger(__name__)


def build_skill_timeseries(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    """
    Explode the skills column and count weekly mentions per skill.
    Returns a long-form DataFrame: skill, ds (week), y (count).
    """
    all_skills = df["skills"].explode().dropna()  # dropna prevents NaN entering top_skills
    top_skills = all_skills.value_counts().head(top_n).index.tolist()

    rows = []
    for skill in top_skills:
        mask = df["skills"].apply(lambda s: skill in s if hasattr(s, "__iter__") and not isinstance(s, str) else False)
        skill_df = df[mask][["week"]].copy()
        skill_df["skill"] = skill
        weekly = skill_df.groupby(["week", "skill"]).size().reset_index(name="y")
        rows.append(weekly)

    if not rows:
        return pd.DataFrame(columns=["ds", "y", "skill"])

    ts = pd.concat(rows, ignore_index=True)
    ts = ts.rename(columns={"week": "ds"})
    ts["ds"] = pd.to_datetime(ts["ds"])
    return ts


def forecast_skill(skill_ts: pd.DataFrame, periods: int = 26) -> pd.DataFrame:
    """
    Fit Holt-Winters additive-trend exponential smoothing on a single skill's
    weekly time-series and project forward.
    Confidence interval is ±1.96 × residual std from in-sample fit.
    Returns columns: ds, yhat, yhat_lower, yhat_upper, trend
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    if len(skill_ts) < 4:
        return pd.DataFrame()

    ts = skill_ts.sort_values("ds").copy()
    y = ts["y"].values.astype(float)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # suppress statsmodels convergence warnings
            model = ExponentialSmoothing(y, trend="add", seasonal=None).fit(optimized=True)
    except Exception as exc:
        logger.warning("ExponentialSmoothing failed (len=%d): %s", len(y), exc)
        return pd.DataFrame()

    fitted = model.fittedvalues
    residual_std = float(np.std(y - fitted, ddof=1)) if len(y) > 1 else 0.0
    margin = 1.96 * residual_std

    # In-sample rows (historical fitted values)
    in_sample = pd.DataFrame({
        "ds": ts["ds"].values,
        "yhat": np.clip(fitted, 0, None),
        "yhat_lower": np.clip(fitted - margin, 0, None),
        "yhat_upper": np.clip(fitted + margin, 0, None),
        "trend": np.clip(fitted, 0, None),
    })

    # Out-of-sample forecast
    point_forecast = model.forecast(periods)
    last_ds = ts["ds"].max()
    future_ds = [last_ds + pd.Timedelta(weeks=i + 1) for i in range(periods)]

    out_of_sample = pd.DataFrame({
        "ds": future_ds,
        "yhat": np.clip(point_forecast, 0, None),
        "yhat_lower": np.clip(point_forecast - margin, 0, None),
        "yhat_upper": np.clip(point_forecast + margin, 0, None),
        "trend": np.clip(point_forecast, 0, None),
    })

    return pd.concat([in_sample, out_of_sample], ignore_index=True)


def forecast_all_skills(
    df: pd.DataFrame,
    top_n: int = 50,
    forecast_periods: int = 26,
    output_path: str = "data/processed/forecasts.parquet",
) -> pd.DataFrame:
    ts = build_skill_timeseries(df, top_n=top_n)
    skills = ts["skill"].unique().tolist()

    all_forecasts = []
    for skill in tqdm(skills, desc="Forecasting skills"):
        skill_ts = ts[ts["skill"] == skill].sort_values("ds")
        forecast = forecast_skill(skill_ts, periods=forecast_periods)
        if forecast.empty:
            continue
        forecast["skill"] = skill
        actuals = skill_ts[["ds", "y"]].copy()
        forecast = forecast.merge(actuals, on="ds", how="left")
        all_forecasts.append(forecast)

    if not all_forecasts:
        return pd.DataFrame()

    result = pd.concat(all_forecasts, ignore_index=True)

    # Compute trend direction: slope of last 8 weeks of trend component
    trend_dirs = []
    for skill in result["skill"].unique():
        skill_data = result[result["skill"] == skill].sort_values("ds").tail(8)
        if len(skill_data) >= 2:
            slope = (skill_data["trend"].iloc[-1] - skill_data["trend"].iloc[0]) / len(skill_data)
            trend_dirs.append({"skill": skill, "trend_slope": slope})

    trend_df = pd.DataFrame(trend_dirs)
    result = result.merge(trend_df, on="skill", how="left")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out, index=False)
    logger.info("Saved forecasts for %d skills to %s", len(skills), out)
    return result
