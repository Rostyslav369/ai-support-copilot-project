from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai_service import AIService
from app.config import settings
from app.database import Base, engine, get_db
from app.document_service import extract_text_from_file, chunk_text
from app.sample_docs import sample_docs_store
from app.schemas import (
    AskRequest,
    AskResponse,
    DeleteResponse,
    DocumentListResponse,
    HealthResponse,
    UploadResponse,
)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.APP_NAME)
ai_service = AIService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()

    Base.metadata.create_all(bind=engine)

    if not ai_service.is_ready():
        print("Gemini API key missing. Skipping sample document loading.")
        return

    from app.database import SessionLocal
    db = SessionLocal()

    try:
        from app.models import Document
        existing_count = db.query(Document).count()

        if existing_count == 0:
            for doc in sample_docs_store:
                chunks = chunk_text(doc["text"])
                ai_service.add_document_chunks(db, doc["filename"], chunks)
            print("Sample documents loaded successfully.")
    except Exception as exc:
        print(f"Skipping sample document loading due to error: {exc}")
    finally:
        db.close()


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.APP_NAME)


@app.get("/documents", response_model=DocumentListResponse)
def get_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    return DocumentListResponse(documents=ai_service.list_documents(db))


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if not ai_service.is_ready():
        raise HTTPException(status_code=500, detail="Gemini API key is missing in backend/.env")

    allowed_types = [".txt", ".md", ".pdf"]
    suffix = Path(file.filename).suffix.lower()

    if suffix not in allowed_types:
        raise HTTPException(status_code=400, detail="Only .txt, .md, and .pdf files are supported.")

    file_path = UPLOAD_DIR / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    try:
        extracted_text = extract_text_from_file(file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(exc)}") from exc

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="The uploaded file did not contain usable text.")

    chunks = chunk_text(extracted_text)
    chunks_added = ai_service.add_document_chunks(db, file.filename, chunks)

    return UploadResponse(
        filename=file.filename,
        chunks_added=chunks_added,
        message="Document uploaded and indexed successfully.",
    )


@app.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    db: Session = Depends(get_db),
) -> AskResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not ai_service.is_ready():
        raise HTTPException(status_code=500, detail="Gemini API key is missing in backend/.env")

    result = ai_service.ask_question(db, payload.question.strip())
    return AskResponse(**result)


@app.delete("/documents/{filename}", response_model=DeleteResponse)
def delete_document(
    filename: str,
    db: Session = Depends(get_db),
) -> DeleteResponse:
    ai_service.remove_document(db, filename)

    target_file = UPLOAD_DIR / filename
    if target_file.exists():
        target_file.unlink()

    return DeleteResponse(
        message="Document removed successfully.",
        deleted_filename=filename,
    )