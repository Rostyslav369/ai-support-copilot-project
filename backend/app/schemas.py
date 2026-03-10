from pydantic import BaseModel
from typing import List, Optional


class HealthResponse(BaseModel):
    status: str
    app: str


class UploadResponse(BaseModel):
    filename: str
    chunks_added: int
    message: str


class AskRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    filename: str
    chunk_index: int
    text: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    confidence: float
    needs_human_review: bool
    sources: List[SourceChunk]


class DocumentListItem(BaseModel):
    filename: str
    chunks: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentListItem]


class DeleteResponse(BaseModel):
    message: str
    deleted_filename: Optional[str] = None