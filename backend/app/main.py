from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from . import models  # noqa: F401
from . import schemas, crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Job Tracker")

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

@app.get("/applications", response_model=list[schemas.JobApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    return crud.list_applications(db)

@app.get("/applications/{app_id}", response_model=schemas.JobApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    app_row = crud.get_application(db, app_id)
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_row

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
