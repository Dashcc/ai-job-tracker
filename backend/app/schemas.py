from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

class JobApplicationBase(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    job_url: Optional[str] = None
    status: str = "Wishlist"
    deadline: Optional[date] = None
    notes: Optional[str] = None

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[date] = None
    notes: Optional[str] = None

class JobApplicationOut(JobApplicationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
