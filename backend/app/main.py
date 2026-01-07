from fastapi import FastAPI
from .db import Base, engine
from . import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Job Tracker")

@app.get("/health")
def health():
    return {"status": "ok"}
