import pytest
import pandas as pd
from src.nlp.cleaner import clean_description, build_master_df, _extract_company, _extract_location
import json
import tempfile
from pathlib import Path


def test_clean_description_strips_html():
    html = "<p>We need a <strong>Python</strong> developer.</p>"
    result = clean_description(html)
    assert "<p>" not in result
    assert "Python" in result


def test_clean_description_removes_boilerplate():
    text = "Great role. We are an equal opportunity employer. Must know Python."
    result = clean_description(text)
    assert "equal opportunity employer" not in result.lower()
    assert "Python" in result


def test_clean_description_collapses_whitespace():
    text = "Python   developer   needed"
    result = clean_description(text)
    assert "  " not in result


def test_clean_description_empty():
    assert clean_description("") == ""
    assert clean_description(None) == ""


def test_extract_company_dict():
    job = {"company": {"display_name": "Acme Corp"}}
    assert _extract_company(job) == "Acme Corp"


def test_extract_company_string():
    job = {"company": "Acme Corp"}
    assert _extract_company(job) == "Acme Corp"


def test_extract_location():
    job = {"location": {"display_name": "New York, NY"}}
    assert _extract_location(job) == "New York, NY"


def test_build_master_df_deduplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        jobs = [
            {"id": "1", "title": "Engineer", "company": {"display_name": "Co"}, "location": {"display_name": "NY"},
             "description": "Python dev", "created": "2024-01-01", "_source": "mock", "_query": "eng", "_scraped_at": "2024-01-01"},
            # duplicate
            {"id": "1", "title": "Engineer", "company": {"display_name": "Co"}, "location": {"display_name": "NY"},
             "description": "Python dev", "created": "2024-01-01", "_source": "mock", "_query": "eng2", "_scraped_at": "2024-01-01"},
            {"id": "2", "title": "Analyst", "company": {"display_name": "Biz"}, "location": {"display_name": "SF"},
             "description": "SQL analyst", "created": "2024-01-02", "_source": "mock", "_query": "analyst", "_scraped_at": "2024-01-02"},
        ]
        p = Path(tmpdir) / "test.jsonl"
        with open(p, "w") as f:
            for j in jobs:
                f.write(json.dumps(j) + "\n")

        df = build_master_df(tmpdir)
        assert len(df) == 2  # deduplicated


def test_build_master_df_empty_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            build_master_df(tmpdir)
