from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_list_applications():
    payload = {
        "company": "TestCo",
        "role": "Data Scientist",
        "status": "Applied",
        "notes": "Python SQL FastAPI",
        "deadline": None
    }
    r = client.post("/applications", json=payload)
    assert r.status_code == 200
    created = r.json()
    assert created["company"] == "TestCo"
    assert "id" in created

    r2 = client.get("/applications")
    assert r2.status_code == 200
    rows = r2.json()
    assert isinstance(rows, list)
    assert any(x["id"] == created["id"] for x in rows)
