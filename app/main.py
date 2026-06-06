from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.staticfiles import StaticFiles

from app.database import init_db, iter_db
from app.schemas import Note, NoteCreate, NoteUpdate


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Notes CI/CD Demo", version="1.0.0", lifespan=lifespan)
Db = Annotated[sqlite3.Connection, Depends(iter_db)]


def row_to_note(row) -> Note:
    return Note(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/notes", response_model=list[Note])
def list_notes(db: Db) -> list[Note]:
    rows = db.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    return [row_to_note(row) for row in rows]


@app.post("/api/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, db: Db) -> Note:
    cursor = db.execute(
        """
        INSERT INTO notes (title, content)
        VALUES (?, ?)
        RETURNING *
        """,
        (payload.title, payload.content),
    )
    row = cursor.fetchone()
    db.commit()
    return row_to_note(row)


@app.patch("/api/notes/{note_id}", response_model=Note)
def update_note(note_id: int, payload: NoteUpdate, db: Db) -> Note:
    existing = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    next_title = payload.title if payload.title is not None else existing["title"]
    next_content = payload.content if payload.content is not None else existing["content"]
    next_completed = (
        int(payload.completed) if payload.completed is not None else existing["completed"]
    )

    cursor = db.execute(
        """
        UPDATE notes
        SET title = ?, content = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        RETURNING *
        """,
        (next_title, next_content, next_completed, note_id),
    )
    row = cursor.fetchone()
    db.commit()
    return row_to_note(row)


@app.delete("/api/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Db) -> Response:
    cursor = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
