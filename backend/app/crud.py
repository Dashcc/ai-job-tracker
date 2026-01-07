from sqlalchemy.orm import Session
from . import models, schemas

def create_application(db: Session, data: schemas.JobApplicationCreate):
    app = models.JobApplication(**data.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

def get_application(db: Session, app_id: int):
    return db.query(models.JobApplication).filter(models.JobApplication.id == app_id).first()

def list_applications(db: Session):
    return db.query(models.JobApplication).order_by(models.JobApplication.created_at.desc()).all()

def update_application(db: Session, app_id: int, data: schemas.JobApplicationUpdate):
    app = get_application(db, app_id)
    if not app:
        return None
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    for k, v in updates.items():
        setattr(app, k, v)
    db.commit()
    db.refresh(app)
    return app

def delete_application(db: Session, app_id: int):
    app = get_application(db, app_id)
    if not app:
        return False
    db.delete(app)
    db.commit()
    return True
