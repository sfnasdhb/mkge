"""
Stage 3: Embedding generation (PROJECT_CONTEXT §9 step 4).
Dùng Gemini text-embedding-004 (768 dims, KHÔNG đổi sau khi có data — §4.3).
"""
import logging
from typing import Sequence

import google.generativeai as genai

from src.mkge.config import settings

logger = logging.getLogger(__name__)


def _configure() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=settings.gemini_api_key)


def _candidate_models() -> list[str]:
    """Thứ tự thử model. Phải start với 'models/' hoặc 'tunedModels/' (Gemini SDK requirement)."""
    candidates = [
        settings.embedding_model,
        "models/gemini-embedding-001",
        "models/gemini-embedding-2",
        "models/gemini-embedding-2-preview",
        "models/text-embedding-004",  # legacy fallback
    ]
    seen, out = set(), []
    for m in candidates:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _embed_one(model: str, text: str, task_type: str) -> list[float]:
    """gemini-embedding-001 trả mặc định 3072 dim — phải truyền output_dimensionality để match Qdrant 768."""
    kwargs = {"model": model, "content": text, "task_type": task_type}
    # Chỉ truyền output_dimensionality cho dòng gemini-embedding-* (text-embedding-004 không support)
    if "gemini-embedding" in model:
        kwargs["output_dimensionality"] = settings.embedding_dims
    resp = genai.embed_content(**kwargs)
    return list(resp["embedding"])


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    _configure()
    last_exc: Exception | None = None
    for model in _candidate_models():
        try:
            return _embed_one(model, text, task_type)
        except Exception as exc:
            last_exc = exc
    raise RuntimeError(f"All embedding models failed; last error: {last_exc}")


def embed_batch(texts: Sequence[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Tìm model còn sống ở lần đầu, dùng lại cho các text sau."""
    _configure()
    if not texts:
        return []

    chosen: str | None = None
    first_vec: list[float] = []
    for model in _candidate_models():
        try:
            first_vec = _embed_one(model, texts[0], task_type)
            chosen = model
            logger.info("Embedding using model='%s'", chosen)
            break
        except Exception as exc:
            logger.warning("Embedding model '%s' failed: %s", model, exc)

    if not chosen:
        logger.warning("All embedding models failed — Qdrant sẽ nhận zero vectors")
        return [[0.0] * settings.embedding_dims for _ in texts]

    out: list[list[float]] = [first_vec]
    for i, text in enumerate(texts[1:], start=1):
        try:
            out.append(_embed_one(chosen, text, task_type))
        except Exception as exc:
            logger.warning("Embedding chunk %d failed: %s — zero vector", i, exc)
            out.append([0.0] * settings.embedding_dims)
    return out
