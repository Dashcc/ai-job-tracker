from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from . import models  # noqa: F401
from . import schemas, crud

from datetime import date
from typing import Optional

import os
from .scoring import load_skills, compute_priority

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Job Tracker")
SKILLS_PATH = os.path.join(os.path.dirname(__file__), "skills.txt")
SKILLS_TEXT = load_skills(SKILLS_PATH)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
STATUSES = ["Wishlist", "Applied", "Interview", "Offer", "Rejection"]



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/applications", response_model=schemas.JobApplicationOut)
def create_application(payload: schemas.JobApplicationCreate, db: Session = Depends(get_db)):
    return crud.create_application(db, payload)

@app.get("/applications", response_model=list[schemas.JobApplicationScored])
def list_applications(db: Session = Depends(get_db)):
    rows = crud.list_applications(db)
    scored = []
    for r in rows:
        s = compute_priority(
            skills_text=SKILLS_TEXT,
            job_text=r.notes,       # for MVP, use notes as “job text”
            deadline=r.deadline,
        )
        scored.append({
            **schemas.JobApplicationOut.model_validate(r).model_dump(),
            "skill_match_score": s.skill_match_score,
            "deadline_urgency_score": s.deadline_urgency_score,
            "priority_score": s.priority_score,
        })
    return scored


@app.get("/applications/{app_id}", response_model=schemas.JobApplicationScored)
def get_application(app_id: int, db: Session = Depends(get_db)):
    r = crud.get_application(db, app_id)
    if not r:
        raise HTTPException(status_code=404, detail="Application not found")

    s = compute_priority(
        skills_text=SKILLS_TEXT,
        job_text=r.notes,
        deadline=r.deadline,
    )
    return {
        **schemas.JobApplicationOut.model_validate(r).model_dump(),
        "skill_match_score": s.skill_match_score,
        "deadline_urgency_score": s.deadline_urgency_score,
        "priority_score": s.priority_score,
    }


@app.put("/applications/{app_id}", response_model=schemas.JobApplicationOut)
def update_application(app_id: int, payload: schemas.JobApplicationUpdate, db: Session = Depends(get_db)):
    updated = crud.update_application(db, app_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated

@app.delete("/applications/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_application(db, app_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"deleted": True}

def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    return date.fromisoformat(s)  # expects YYYY-MM-DD

@app.get("/")
def dashboard(
    request: Request,
    status: str = "",
    sort: str = "priority",
    db: Session = Depends(get_db),
):
    rows = crud.list_applications(db)

    # filter
    if status:
        rows = [r for r in rows if r.status == status]

    # score all (for sorting + display)
    scored = []
    for r in rows:
        s = compute_priority(SKILLS_TEXT, r.notes, r.deadline)
        scored.append({
            **schemas.JobApplicationOut.model_validate(r).model_dump(),
            "skill_match_score": s.skill_match_score,
            "deadline_urgency_score": s.deadline_urgency_score,
            "priority_score": s.priority_score,
        })

    # sort
    if sort == "deadline":
        scored.sort(key=lambda x: (x["deadline"] is None, x["deadline"]))  # None last
    elif sort == "created":
        scored.sort(key=lambda x: x["created_at"], reverse=True)
    else:
        scored.sort(key=lambda x: x["priority_score"], reverse=True)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "applications": scored,
            "statuses": STATUSES,
            "status_filter": status,
            "sort_mode": sort,
        },
    )


@app.get("/new")
def new_form(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "heading": "New application", "action": "/new", "app": None, "statuses": STATUSES},
    )


@app.post("/new")
def create_from_form(
    company: str = Form(...),
    role: str = Form(...),
    location: str = Form(""),
    job_url: str = Form(""),
    status: str = Form("Wishlist"),
    deadline: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    payload = schemas.JobApplicationCreate(
        company=company,
        role=role,
        location=location or None,
        job_url=job_url or None,
        status=status,
        deadline=parse_date(deadline),
        notes=notes or None,
    )
    crud.create_application(db, payload)
    return RedirectResponse(url="/", status_code=303)


@app.get("/view/{app_id}")
def view_app(app_id: int, request: Request, db: Session = Depends(get_db)):
    r = crud.get_application(db, app_id)
    if not r:
        raise HTTPException(status_code=404, detail="Application not found")

    s = compute_priority(SKILLS_TEXT, r.notes, r.deadline)
    app_scored = {
        **schemas.JobApplicationOut.model_validate(r).model_dump(),
        "skill_match_score": s.skill_match_score,
        "deadline_urgency_score": s.deadline_urgency_score,
        "priority_score": s.priority_score,
    }

    return templates.TemplateResponse("view.html", {"request": request, "app": app_scored})


@app.get("/edit/{app_id}")
def edit_form(app_id: int, request: Request, db: Session = Depends(get_db)):
    r = crud.get_application(db, app_id)
    if not r:
        raise HTTPException(status_code=404, detail="Application not found")

    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "heading": "Edit application",
            "action": f"/edit/{app_id}",
            "app": schemas.JobApplicationOut.model_validate(r).model_dump(),
            "statuses": STATUSES,
        },
    )


@app.post("/edit/{app_id}")
def edit_from_form(
    app_id: int,
    company: str = Form(...),
    role: str = Form(...),
    location: str = Form(""),
    job_url: str = Form(""),
    status: str = Form("Wishlist"),
    deadline: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    payload = schemas.JobApplicationUpdate(
        company=company,
        role=role,
        location=location or None,
        job_url=job_url or None,
        status=status,
        deadline=parse_date(deadline),
        notes=notes or None,
    )
    updated = crud.update_application(db, app_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return RedirectResponse(url=f"/view/{app_id}", status_code=303)


@app.post("/delete/{app_id}")
def delete_from_ui(app_id: int, db: Session = Depends(get_db)):
    crud.delete_application(db, app_id)
    return RedirectResponse(url="/", status_code=303)
