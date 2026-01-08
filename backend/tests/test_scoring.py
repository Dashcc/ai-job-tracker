from datetime import date, timedelta
from app.scoring import compute_priority

def test_priority_increases_with_deadline_urgency():
    skills = "python sql fastapi"
    job = "We need a Python developer with FastAPI and SQL experience."
    far = date.today() + timedelta(days=30)
    near = date.today() + timedelta(days=3)

    s_far = compute_priority(skills, job, far)
    s_near = compute_priority(skills, job, near)

    assert s_near.deadline_urgency_score > s_far.deadline_urgency_score
    assert s_near.priority_score >= s_far.priority_score

def test_skill_match_zero_when_no_job_text():
    skills = "python sql"
    s = compute_priority(skills, "", None)
    assert s.skill_match_score == 0.0
    assert s.priority_score >= 0
