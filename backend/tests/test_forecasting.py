import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.forecasting.demand import build_skill_timeseries, forecast_skill


def _make_df(n_weeks: int = 20) -> pd.DataFrame:
    base = datetime(2024, 1, 1)
    records = []
    skills_pool = [["Python", "SQL"], ["Python", "TensorFlow"], ["SQL", "dbt"], ["React", "TypeScript"]]
    for i in range(n_weeks * 5):
        week = base + timedelta(weeks=i % n_weeks)
        records.append({
            "skills": skills_pool[i % len(skills_pool)],
            "week": pd.Timestamp(week),
            "title": "Data Scientist",
        })
    return pd.DataFrame(records)


def test_build_skill_timeseries_shape():
    df = _make_df()
    ts = build_skill_timeseries(df, top_n=3)
    assert not ts.empty
    assert "ds" in ts.columns
    assert "y" in ts.columns
    assert "skill" in ts.columns


def test_build_skill_timeseries_top_skills():
    df = _make_df()
    ts = build_skill_timeseries(df, top_n=2)
    skills_found = ts["skill"].unique()
    assert len(skills_found) <= 2


def test_forecast_skill_returns_forecast():
    # Build a simple time-series with enough data points
    dates = pd.date_range("2023-01-01", periods=26, freq="W")
    ts = pd.DataFrame({"ds": dates, "y": np.random.randint(1, 10, 26)})
    result = forecast_skill(ts, periods=8)
    assert not result.empty
    assert "yhat" in result.columns
    assert "ds" in result.columns
    # Forecast should extend beyond last actual date
    assert result["ds"].max() > ts["ds"].max()


def test_forecast_skill_insufficient_data():
    ts = pd.DataFrame({"ds": pd.date_range("2024-01-01", periods=2, freq="W"), "y": [1, 2]})
    result = forecast_skill(ts)
    assert result.empty


def test_forecast_yhat_non_negative():
    dates = pd.date_range("2023-01-01", periods=30, freq="W")
    ts = pd.DataFrame({"ds": dates, "y": np.ones(30)})
    result = forecast_skill(ts, periods=10)
    assert (result["yhat"] >= 0).all()
    assert (result["yhat_lower"] >= 0).all()
