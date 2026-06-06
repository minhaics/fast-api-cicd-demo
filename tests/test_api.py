import os

from fastapi.testclient import TestClient


def test_note_crud_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_DB_PATH", str(tmp_path / "test.db"))

    from app.main import app

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        created = client.post(
            "/api/notes",
            json={"title": "Learn CI/CD", "content": "Run tests before deploy"},
        )
        assert created.status_code == 201
        note = created.json()
        assert note["title"] == "Learn CI/CD"
        assert note["completed"] is False

        listed = client.get("/api/notes")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        updated = client.patch(f"/api/notes/{note['id']}", json={"completed": True})
        assert updated.status_code == 200
        assert updated.json()["completed"] is True

        deleted = client.delete(f"/api/notes/{note['id']}")
        assert deleted.status_code == 204

        empty = client.get("/api/notes")
        assert empty.json() == []
