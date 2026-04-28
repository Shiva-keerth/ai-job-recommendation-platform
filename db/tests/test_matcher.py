"""
Basic unit tests for the AI matcher.
Run with: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ai_matcher import (
    _split_skills, _is_soft, _weighted_fraction,
    _compute_final_scores, _score_one_job,
)


def test_split_skills_comma():
    assert _split_skills("python, sql, pandas") == ["python", "sql", "pandas"]

def test_split_skills_pipe():
    assert _split_skills("java|spring|docker") == ["java", "spring", "docker"]

def test_split_skills_empty():
    assert _split_skills("") == []
    assert _split_skills(None) == []

def test_is_soft():
    assert _is_soft("communication") is True
    assert _is_soft("python") is False
    assert _is_soft("leadership") is True

def test_weighted_fraction_perfect():
    skills = ["python", "sql", "pandas"]
    resume = {"python", "sql", "pandas"}
    assert _weighted_fraction(skills, resume) == 1.0

def test_weighted_fraction_zero():
    skills = ["python", "sql"]
    resume = {"java"}
    assert _weighted_fraction(skills, resume) == 0.0

def test_weighted_fraction_partial():
    skills = ["python", "sql", "pandas"]
    resume = {"python", "sql"}
    frac   = _weighted_fraction(skills, resume)
    assert 0.6 < frac < 0.75

def test_soft_skill_weighted_less():
    hard_only = ["python", "sql"]
    with_soft  = ["python", "sql", "communication"]
    resume     = {"python", "sql"}
    frac_hard  = _weighted_fraction(hard_only, resume)
    frac_mixed = _weighted_fraction(with_soft, resume)
    # matched fraction of mixed should be < pure hard (denominator is bigger)
    assert frac_mixed <= frac_hard

def test_three_scores_ordering():
    r, o, a = _compute_final_scores(
        core_match=0.8, secondary_match=0.6,
        tfidf_sim=0.5, missing_core_count=1, core_count=6,
        exp_score=0.5, project_score=0.5, cert_score=0.5,
    )
    assert o >= r >= a, "Optimistic >= Recruiter >= ATS must hold"

def test_three_scores_bounds():
    r, o, a = _compute_final_scores(1.0, 1.0, 1.0, 0, 6, 1.0, 1.0, 1.0)
    assert 0.0 <= r <= 1.0
    assert 0.0 <= o <= 1.0
    assert 0.0 <= a <= 1.0

def test_three_scores_zero():
    r, o, a = _compute_final_scores(0.0, 0.0, 0.0, 6, 6, 0.0, 0.0, 0.0)
    assert r == 0.0
    assert o >= 0.0
    assert a == 0.0

def test_score_one_job_all_match():
    required     = ["python", "sql", "pandas", "numpy", "tableau", "excel"]
    resume_skills= set(required)
    result = _score_one_job(required, resume_skills)
    assert result["core_match"] == 1.0
    assert len(result["missing_skills"]) == 0
    assert len(result["matched_skills"]) == len(required)

def test_score_one_job_no_match():
    required      = ["python", "sql", "pandas"]
    resume_skills = {"java", "spring"}
    result = _score_one_job(required, resume_skills)
    assert result["core_match"] == 0.0
    assert len(result["missing_skills"]) == len(required)