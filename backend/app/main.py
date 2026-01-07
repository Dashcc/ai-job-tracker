from fastapi import FastAPI

app = FastAPI(title="AI Job Tracker")

@app.get("/health")
def health():
    return {"status": "ok"}
