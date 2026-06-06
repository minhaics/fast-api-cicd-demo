# Notes CI/CD Demo

Project fullstack nhỏ để học CI/CD với FastAPI:

- Backend: FastAPI REST API.
- Database: SQLite.
- Frontend: HTML/CSS/JavaScript tĩnh, được FastAPI serve trực tiếp.
- Test: pytest + FastAPI TestClient.
- Container: Dockerfile + docker-compose.
- CI/CD: GitHub Actions trong `.github/workflows/ci-cd.yml`.

## Chạy Local Bằng Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Mở:

- App: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Chạy Test

```bash
pytest -q
```

## Chạy Bằng Docker

```bash
docker compose up --build
```

Mở http://localhost:8000.
