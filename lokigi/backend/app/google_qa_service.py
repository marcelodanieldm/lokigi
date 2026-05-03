"""Google Q&A Manager Service.

Two responsibilities:
  1. RAG engine — simplified Retrieval Augmented Generation that uses the
     business_context table (menu, description, faq pairs) to auto-answer
     incoming customer questions via TF-IDF cosine similarity.
  2. Monitoring — polls the Google Business Profile Q&A API for new
     unanswered questions, runs the RAG engine, and persists results.

Confidence threshold for auto-answer: 80.0 (configurable via QA_CONFIDENCE_THRESHOLD).
"""
from __future__ import annotations

import logging
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import engine
from .google_client import GoogleBusinessProfileClient, GoogleOAuthError
from .models import BusinessContext, GoogleConnection, GoogleQAQuestion
from .services import ensure_valid_access_token

logger = logging.getLogger(__name__)

QA_CONFIDENCE_THRESHOLD = 80.0  # Minimum % confidence to auto-answer


# ── Text utilities ────────────────────────────────────────────────────────────

_STOP_WORDS_ES = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "es",
    "se", "por", "con", "para", "que", "del", "al", "su", "lo", "me",
    "te", "le", "nos", "les", "si", "no", "mi", "tu", "hay", "ser",
    "como", "pero", "o", "e", "ni", "son", "más", "ya", "este", "esta",
    "están", "tiene", "tienen", "qué", "cuál", "cuáles", "dónde", "cómo",
    "cuánto", "cuándo", "quién", "quiénes", "cuántos",
}


def _normalize(text: str) -> str:
    """Lowercase, strip accents, remove punctuation."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]", " ", ascii_text)


def _tokenize(text: str) -> list[str]:
    tokens = _normalize(text).split()
    return [t for t in tokens if t not in _STOP_WORDS_ES and len(t) > 1]


def _tf(tokens: list[str]) -> Counter:
    return Counter(tokens)


def _idf(corpus_tokens: list[list[str]]) -> dict[str, float]:
    """Compute inverse document frequency for a corpus of token lists."""
    n = len(corpus_tokens)
    df: Counter = Counter()
    for doc in corpus_tokens:
        for term in set(doc):
            df[term] += 1
    return {term: math.log((n + 1) / (freq + 1)) + 1.0 for term, freq in df.items()}


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = _tf(tokens)
    return {term: freq * idf.get(term, 1.0) for term, freq in tf.items()}


def _cosine_sim(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[t] * vec_b[t] for t in common)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── RAG Engine ────────────────────────────────────────────────────────────────

class RAGResult:
    __slots__ = ("answer", "confidence", "context_id")

    def __init__(self, answer: str, confidence: float, context_id: UUID | None) -> None:
        self.answer = answer
        self.confidence = confidence  # 0.0 – 100.0
        self.context_id = context_id


def run_rag(question: str, context_entries: list[BusinessContext]) -> RAGResult:
    """Search business context to find the best answer for a question.

    Strategy:
      1. Build a searchable corpus from every active context entry.
         - For 'faq' entries the corpus document is ``faq_question + ' ' + content``.
         - For 'menu' / 'description' entries the corpus document is ``content``.
      2. Compute TF-IDF vectors for the question and each document.
      3. Return the entry with the highest cosine similarity.
      4. Scale similarity (0–1) to a 0–100 confidence score with a small
         bonus for exact faq question matches.
    """
    if not context_entries:
        return RAGResult(answer="", confidence=0.0, context_id=None)

    # Build corpus
    docs: list[tuple[BusinessContext, str]] = []
    for entry in context_entries:
        if entry.context_type == "faq":
            doc_text = f"{entry.faq_question or ''} {entry.content}"
        else:
            doc_text = entry.content
        docs.append((entry, doc_text))

    all_tokens = [_tokenize(doc_text) for _, doc_text in docs]
    question_tokens = _tokenize(question)

    # IDF trained on corpus + question
    idf = _idf(all_tokens + [question_tokens])

    q_vec = _tfidf_vector(question_tokens, idf)

    best_sim = -1.0
    best_entry: BusinessContext | None = None

    for (entry, _), doc_toks in zip(docs, all_tokens):
        d_vec = _tfidf_vector(doc_toks, idf)
        sim = _cosine_sim(q_vec, d_vec)
        if sim > best_sim:
            best_sim = sim
            best_entry = entry

    if best_entry is None:
        return RAGResult(answer="", confidence=0.0, context_id=None)

    # Scale to 0-100; cosine similarity is already [0,1]
    confidence = round(min(best_sim * 110.0, 100.0), 2)

    return RAGResult(
        answer=best_entry.content,
        confidence=confidence,
        context_id=best_entry.id,
    )


# ── Monitoring Service ────────────────────────────────────────────────────────

class GoogleQAService:
    """High-level service wiring GBP Q&A polling + RAG auto-answer."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._client = GoogleBusinessProfileClient(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
        )

    # ── Context management ────────────────────────────────────────────────────

    def list_context(self, user_id: UUID) -> list[BusinessContext]:
        return list(
            self._db.scalars(
                select(BusinessContext)
                .where(BusinessContext.user_id == user_id, BusinessContext.is_active.is_(True))
                .order_by(BusinessContext.context_type, BusinessContext.created_at)
            ).all()
        )

    def upsert_context(
        self,
        user_id: UUID,
        location_id: str,
        context_type: str,
        content: str,
        faq_question: str | None = None,
        entry_id: UUID | None = None,
    ) -> BusinessContext:
        if entry_id:
            entry = self._db.get(BusinessContext, entry_id)
            if not entry or entry.user_id != user_id:
                raise ValueError("Context entry not found or unauthorized")
        else:
            entry = BusinessContext(user_id=user_id, location_id=location_id)
            self._db.add(entry)

        entry.context_type = context_type
        entry.content = content.strip()
        entry.faq_question = faq_question.strip() if faq_question else None
        entry.is_active = True
        self._db.commit()
        self._db.refresh(entry)
        return entry

    def delete_context(self, user_id: UUID, entry_id: UUID) -> None:
        entry = self._db.get(BusinessContext, entry_id)
        if not entry or entry.user_id != user_id:
            raise ValueError("Context entry not found or unauthorized")
        entry.is_active = False
        self._db.commit()

    # ── Q&A question listing ──────────────────────────────────────────────────

    def list_questions(
        self,
        user_id: UUID,
        status_filter: str | None = None,
        limit: int = 50,
    ) -> list[GoogleQAQuestion]:
        stmt = (
            select(GoogleQAQuestion)
            .where(GoogleQAQuestion.user_id == user_id)
            .order_by(GoogleQAQuestion.detected_at.desc())
            .limit(limit)
        )
        if status_filter:
            stmt = stmt.where(GoogleQAQuestion.status == status_filter)
        return list(self._db.scalars(stmt).all())

    # ── Polling ───────────────────────────────────────────────────────────────

    async def poll_and_process(self, user_id: UUID) -> dict[str, int]:
        """Poll GBP for new questions and run RAG on each unseen one.

        Returns a summary dict: {new: int, auto_answered: int, needs_intervention: int}.
        """
        connection = self._db.scalar(
            select(GoogleConnection).where(GoogleConnection.user_id == user_id)
        )
        if not connection:
            raise ValueError("No Google connection found for this user")

        access_token = await ensure_valid_access_token(self._db, connection)
        location_name = f"{connection.google_account_name}/locations/{connection.location_id}"

        raw_questions = await self._client.list_questions(
            access_token=access_token,
            location_name=location_name,
            page_size=20,
        )

        context_entries = self.list_context(user_id)

        stats = {"new": 0, "auto_answered": 0, "needs_intervention": 0}

        for raw_q in raw_questions:
            q_name: str = raw_q.get("name", "")
            q_text: str = (raw_q.get("text") or "").strip()
            if not q_name or not q_text:
                continue

            # Skip already-tracked questions
            existing = self._db.scalar(
                select(GoogleQAQuestion).where(GoogleQAQuestion.google_question_id == q_name)
            )
            if existing:
                continue

            # Skip if already answered by owner in Google
            existing_answers = raw_q.get("topAnswers") or raw_q.get("answers") or []
            author_answers = [
                a for a in existing_answers
                if (a.get("author") or {}).get("type") == "MERCHANT"
            ]
            if author_answers:
                continue

            stats["new"] += 1
            now = datetime.now(timezone.utc)

            # Build question record
            create_time_str = raw_q.get("createTime") or raw_q.get("updateTime") or ""
            try:
                detected_at = datetime.fromisoformat(create_time_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                detected_at = now

            author_info = raw_q.get("author") or {}
            question = GoogleQAQuestion(
                user_id=user_id,
                location_id=connection.location_id,
                google_question_id=q_name,
                question_text=q_text,
                author_display_name=author_info.get("displayName"),
                upvote_count=raw_q.get("upvoteCount", 0),
                detected_at=detected_at,
                raw_payload=raw_q,
                status="pending",
            )
            self._db.add(question)
            self._db.flush()

            # Run RAG
            result = run_rag(q_text, context_entries)
            question.auto_answer_text = result.answer or None
            question.answer_confidence = result.confidence if result.answer else None
            question.matched_context_id = result.context_id

            if result.answer and result.confidence >= QA_CONFIDENCE_THRESHOLD:
                question.status = "auto_answered"
                question.answered_at = now
                stats["auto_answered"] += 1
            else:
                question.status = "needs_intervention"
                stats["needs_intervention"] += 1

        self._db.commit()
        return stats

    # ── Sending answers ───────────────────────────────────────────────────────

    async def send_answer(
        self,
        user_id: UUID,
        question_id: UUID,
        answer_text: str,
    ) -> GoogleQAQuestion:
        """Post an answer to Google and mark the question as user_answered."""
        question = self._db.get(GoogleQAQuestion, question_id)
        if not question or question.user_id != user_id:
            raise ValueError("Question not found or unauthorized")

        connection = self._db.scalar(
            select(GoogleConnection).where(GoogleConnection.user_id == user_id)
        )
        if not connection:
            raise ValueError("No Google connection found for this user")

        access_token = await ensure_valid_access_token(self._db, connection)
        await self._client.post_qa_answer(
            access_token=access_token,
            question_name=question.google_question_id,
            answer_text=answer_text.strip(),
        )

        now = datetime.now(timezone.utc)
        question.sent_answer_text = answer_text.strip()
        question.sent_at = now
        question.status = "user_answered"
        question.answered_at = question.answered_at or now
        self._db.commit()
        self._db.refresh(question)
        return question

    async def approve_and_send_auto_answer(
        self,
        user_id: UUID,
        question_id: UUID,
        edited_text: str | None = None,
    ) -> GoogleQAQuestion:
        """Approve the auto-generated answer (optionally edited) and post it."""
        question = self._db.get(GoogleQAQuestion, question_id)
        if not question or question.user_id != user_id:
            raise ValueError("Question not found or unauthorized")
        if not question.auto_answer_text and not edited_text:
            raise ValueError("No answer text available to send")

        final_text = (edited_text or question.auto_answer_text or "").strip()
        return await self.send_answer(user_id=user_id, question_id=question_id, answer_text=final_text)

    def ignore_question(self, user_id: UUID, question_id: UUID) -> GoogleQAQuestion:
        question = self._db.get(GoogleQAQuestion, question_id)
        if not question or question.user_id != user_id:
            raise ValueError("Question not found or unauthorized")
        question.status = "ignored"
        self._db.commit()
        self._db.refresh(question)
        return question


# ── Standalone scheduler task ─────────────────────────────────────────────────

async def run_qa_poll_all_users() -> None:
    """Poll Q&A for all connected users. Intended to be called by APScheduler."""
    with Session(engine) as db:
        connections = list(db.scalars(select(GoogleConnection)).all())
        for conn in connections:
            service = GoogleQAService(db)
            try:
                stats = await service.poll_and_process(conn.user_id)
                logger.info(
                    "Q&A poll user=%s: new=%d auto=%d intervention=%d",
                    conn.user_id,
                    stats["new"],
                    stats["auto_answered"],
                    stats["needs_intervention"],
                )
            except GoogleOAuthError:
                logger.warning("Q&A poll OAuth error for user %s", conn.user_id)
            except Exception:
                logger.exception("Q&A poll unexpected error for user %s", conn.user_id)
