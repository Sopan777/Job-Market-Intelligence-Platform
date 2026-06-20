import pytest
import pandas as pd
from src.nlp.extractor import load_skills_vocabulary, extract_skills, build_matcher
import spacy


@pytest.fixture(scope="module")
def nlp_and_matcher():
    nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
    skills = load_skills_vocabulary()
    matcher = build_matcher(skills, nlp)
    skill_lookup = {s.lower(): s for s in skills}
    return nlp, matcher, skill_lookup


def test_load_skills_fallback():
    skills = load_skills_vocabulary(skills_path=None)
    assert len(skills) > 100
    assert "Python" in skills


def test_extract_skills_finds_known_skills(nlp_and_matcher):
    nlp, matcher, skill_lookup = nlp_and_matcher
    text = "We need experience with Python, machine learning, and SQL."
    found = extract_skills(text, matcher, nlp, skill_lookup)
    assert "Python" in found
    assert any("sql" in s.lower() for s in found)


def test_extract_skills_preserves_casing(nlp_and_matcher):
    nlp, matcher, skill_lookup = nlp_and_matcher
    text = "Experience with Python and TensorFlow required."
    found = extract_skills(text, matcher, nlp, skill_lookup)
    assert "Python" in found
    assert "TensorFlow" in found


def test_extract_skills_empty_text(nlp_and_matcher):
    nlp, matcher, skill_lookup = nlp_and_matcher
    assert extract_skills("", matcher, nlp, skill_lookup) == []
    assert extract_skills(None, matcher, nlp, skill_lookup) == []


def test_extract_skills_no_false_positives(nlp_and_matcher):
    nlp, matcher, skill_lookup = nlp_and_matcher
    text = "We offer competitive salary and great work-life balance."
    found = extract_skills(text, matcher, nlp, skill_lookup)
    # Should not pick up generic non-skill words
    assert "salary" not in found
    assert "balance" not in found
