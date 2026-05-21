"""
Pipeline orchestrator. Tuân theo PROJECT_CONTEXT §9 Pipeline 1:

  1. parse_pdf:           Gemini → Markdown + page-aware Chunks
  2. extract_entities:    Structural NER (heading-aware) + structural inference
  3. verify_relations:    Llama 4 (Groq) → confidence ≥ threshold
  4. generate_embeddings: Gemini text-embedding-004 per chunk
  5. persist_graph:       Cypher + Qdrant upsert
  6. update_status:       Postgres status = 'done'

Steps 1-3 ở module này (build_extraction_result).
Steps 4-5 ở tasks.py vì cần Neo4j/Qdrant async drivers.
"""
import logging
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Sequence

from src.mkge.application.pipeline.extractor import parse_document
from src.mkge.application.pipeline.structural import extract_with_structure
from src.mkge.application.pipeline.verifier import verify_relationships
from src.mkge.domain.entities.chunk import Chunk
from src.mkge.domain.entities.graph import MedicalEntity, Relationship


def _strip_diacritics(s: str) -> str:
    """Chuẩn hoá tiếng Việt: bỏ dấu + lowercase, để so sánh với normalized_name."""
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Kết quả pipeline trước khi persist."""
    markdown: str
    chunks: list[Chunk]
    entities: list[MedicalEntity]
    relationships: list[Relationship]  # đã verified
    mentions: list[tuple[uuid.UUID, uuid.UUID]]  # (chunk_id, entity_id)


def _assign_source_chunks(
    relationships: Sequence[Relationship],
    chunks: Sequence[Chunk],
    entities: Sequence[MedicalEntity],
) -> list[Relationship]:
    """
    Cho mỗi relationship, tìm các chunk có chứa cả source.name VÀ target.name trong text.
    Đây là evidence vật lý (không LLM bịa) → cấu thành anti-hallucination.
    """
    entity_by_id = {e.id: e for e in entities}
    # Pre-strip diacritics khỏi chunk text để match với normalized_name (đã bỏ dấu)
    chunks_stripped = [(c.id, _strip_diacritics(c.text)) for c in chunks]

    out: list[Relationship] = []
    for rel in relationships:
        src = entity_by_id.get(rel.source_id)
        tgt = entity_by_id.get(rel.target_id)
        if not src or not tgt:
            continue
        chunk_ids: list[uuid.UUID] = []
        src_norm = src.normalized_name
        tgt_norm = tgt.normalized_name
        for cid, ctext in chunks_stripped:
            if src_norm in ctext and tgt_norm in ctext:
                chunk_ids.append(cid)
        # Fallback: chunk chứa source (nếu không có chunk nào chứa cả 2)
        if not chunk_ids:
            for cid, ctext in chunks_stripped:
                if src_norm in ctext:
                    chunk_ids.append(cid)
                    break
        out.append(rel.model_copy(update={"source_chunk_ids": chunk_ids}))
    return out


def _build_mentions(
    chunks: Sequence[Chunk], entities: Sequence[MedicalEntity]
) -> list[tuple[uuid.UUID, uuid.UUID]]:
    """Mentions = (chunk_id, entity_id) khi entity.normalized_name xuất hiện trong chunk.text."""
    out: list[tuple[uuid.UUID, uuid.UUID]] = []
    for c in chunks:
        text_stripped = _strip_diacritics(c.text)
        for e in entities:
            if e.normalized_name and e.normalized_name in text_stripped:
                out.append((c.id, e.id))
    return out


def build_extraction_result(
    file_path: str, document_id: uuid.UUID
) -> ExtractionResult:
    """
    Pipeline chính từ file PDF → ExtractionResult sẵn sàng persist.
    """
    # Step 1: Parse PDF → Markdown + page-aware chunks
    markdown, chunks = parse_document(file_path, document_id)
    if not markdown:
        logger.warning("Pipeline: empty markdown from %s", file_path)
        return ExtractionResult(
            markdown="", chunks=chunks, entities=[], relationships=[], mentions=[]
        )

    # Step 2: Structural extraction (NER + ontology inference)
    entities, raw_relationships, _section_map = extract_with_structure(markdown, document_id)
    logger.info("Pre-verify: %d entities, %d raw rels", len(entities), len(raw_relationships))

    # Step 3: Verify relationships (Llama)
    verified_rels = verify_relationships(entities, raw_relationships)
    logger.info("Post-verify: %d rels", len(verified_rels))

    # Step 3b: Anti-hallucination — gắn source_chunk_ids cho mỗi rel
    verified_rels = _assign_source_chunks(verified_rels, chunks, entities)

    # Step 3c: drop rels không có source_chunk_ids (PROJECT_CONTEXT §9 anti-hallucination)
    final_rels = [r for r in verified_rels if r.source_chunk_ids]
    dropped = len(verified_rels) - len(final_rels)
    if dropped:
        logger.info("Dropped %d rel(s) without source_chunk_ids (anti-hallucination)", dropped)

    # Mentions
    mentions = _build_mentions(chunks, entities)

    return ExtractionResult(
        markdown=markdown,
        chunks=chunks,
        entities=entities,
        relationships=final_rels,
        mentions=mentions,
    )


# --- Backward-compat (cho test_gemini.py + code cũ) -----------------------

def run_pipeline_on_file(
    file_path: str, document_id: uuid.UUID
) -> tuple[list[MedicalEntity], list[Relationship]]:
    """Backward-compat: chỉ trả entities + rels."""
    result = build_extraction_result(file_path, document_id)
    return result.entities, result.relationships


def build_graph_from_text(
    text: str, document_id: uuid.UUID
) -> tuple[list[MedicalEntity], list[Relationship]]:
    """Backward-compat cho test_gemini.py: extract trực tiếp từ text (không chunks)."""
    entities, raw_rels, _ = extract_with_structure(text, document_id)
    verified = verify_relationships(entities, raw_rels)
    return entities, verified
