from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List

from google import genai
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, DocumentChunk, SupportQuestion


@dataclass
class RetrievedChunk:
    filename: str
    chunk_index: int
    text: str
    similarity: float


class AIService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    def is_ready(self) -> bool:
        return self.client is not None

    def add_document_chunks(self, db: Session, filename: str, chunks: list[str]) -> int:
        if not self.client:
            raise RuntimeError("Gemini API key is missing.")

        existing = db.query(Document).filter(Document.filename == filename).first()
        if existing:
            db.delete(existing)
            db.commit()

        document = Document(filename=filename)
        db.add(document)
        db.commit()
        db.refresh(document)

        created_count = 0

        for index, chunk in enumerate(chunks):
            embedding = self._embed_text(chunk)
            chunk_row = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                text=chunk,
                embedding=embedding,
            )
            db.add(chunk_row)
            created_count += 1

        db.commit()
        return created_count

    def remove_document(self, db: Session, filename: str) -> None:
        document = db.query(Document).filter(Document.filename == filename).first()
        if document:
            db.delete(document)
            db.commit()

    def list_documents(self, db: Session) -> list[dict]:
        docs = db.query(Document).all()
        result = []

        for doc in docs:
            result.append(
                {
                    "filename": doc.filename,
                    "chunks": len(doc.chunks),
                }
            )

        return sorted(result, key=lambda x: x["filename"])

    def ask_question(self, db: Session, question: str, top_k: int = 3) -> dict:
        if not self.client:
            raise RuntimeError("Gemini API key is missing.")

        all_chunks = db.query(DocumentChunk).join(Document).all()
        if not all_chunks:
            return {
                "answer": "No support documents are loaded yet. Please upload at least one document first.",
                "confidence": 0.0,
                "needs_human_review": True,
                "sources": [],
            }

        query_embedding = self._embed_text(question)
        ranked = self._retrieve(query_embedding, all_chunks, top_k=top_k)

        context = "\n\n".join(
            [
                f"[Source: {item.filename} | chunk {item.chunk_index}]\n{item.text}"
                for item in ranked
            ]
        )

        prompt = (
            "You are an AI customer support copilot for a small business.\n"
            "Answer the user's question using ONLY the provided support documentation.\n"
            "If the answer is not fully supported by the documents, say that the information is not available "
            "and recommend human review.\n"
            "Keep answers clear, helpful, and professional.\n\n"
            f"Customer question:\n{question}\n\n"
            f"Support documentation:\n{context}\n\n"
            "Return a helpful answer grounded in the documents."
        )

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        answer = response.text or "No answer generated."

        confidence = self._estimate_confidence(ranked)
        needs_human_review = confidence < 0.55 or "not available" in answer.lower()

        question_row = SupportQuestion(
            question=question,
            answer=answer,
            confidence=round(confidence, 2),
            needs_human_review=needs_human_review,
        )
        db.add(question_row)
        db.commit()

        return {
            "answer": answer,
            "confidence": round(confidence, 2),
            "needs_human_review": needs_human_review,
            "sources": [
                {
                    "filename": item.filename,
                    "chunk_index": item.chunk_index,
                    "text": item.text,
                    "similarity": round(item.similarity, 3),
                }
                for item in ranked
            ],
        }

    def _embed_text(self, text: str) -> list[float]:
        result = self.client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=text,
        )

        if not result.embeddings or not result.embeddings[0].values:
            raise RuntimeError("Failed to generate embedding.")

        values = list(result.embeddings[0].values)

        if len(values) != 3072:
            raise RuntimeError(f"Expected embedding length 3072, got {len(values)}.")

        return values

    def _retrieve(self, query_embedding: list[float], chunks: list[DocumentChunk], top_k: int = 3) -> List[RetrievedChunk]:
        scored: list[RetrievedChunk] = []

        for chunk in chunks:
            score = self._cosine_similarity(query_embedding, list(chunk.embedding))
            scored.append(
                RetrievedChunk(
                    filename=chunk.document.filename,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    similarity=score,
                )
            )

        scored.sort(key=lambda x: x.similarity, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    @staticmethod
    def _estimate_confidence(results: List[RetrievedChunk]) -> float:
        if not results:
            return 0.0

        avg_score = sum(item.similarity for item in results) / len(results)

        if avg_score >= 0.8:
            return 0.95
        if avg_score >= 0.7:
            return 0.82
        if avg_score >= 0.6:
            return 0.68
        if avg_score >= 0.5:
            return 0.54
        return 0.35