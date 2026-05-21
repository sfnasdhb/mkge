"""
Stage 4: Structural extraction (Hướng 3 - Ontology-based).
Parse Markdown heading tree, phát hiện "topic disease" của từng section,
suy luận quan hệ TREATS/HAS_SYMPTOM/CAUSES_SE từ vị trí entity trong cấu trúc.

Mọi relationship suy luận đều có evidence là HEADING TEXT (không phải LLM bịa)
→ Verifier ở Stage 3 vẫn validate trước khi ghi Neo4j.
"""
import json
import logging
import re
import uuid
from dataclasses import dataclass, field

from src.mkge.application.pipeline.ner import _ner_via_gemini, _ner_via_groq, _is_quota_error
from src.mkge.config import settings
from src.mkge.domain.entities.graph import (
    EntityType,
    MedicalEntity,
    RelationType,
    Relationship,
)

logger = logging.getLogger(__name__)


@dataclass
class Section:
    level: int
    title: str
    body: str = ""
    parent: "Section | None" = None
    children: list["Section"] = field(default_factory=list)

    def heading_path(self) -> list[str]:
        path = []
        cur: Section | None = self
        while cur and cur.title:
            path.insert(0, cur.title)
            cur = cur.parent
        return path

    def full_text(self) -> str:
        """Heading path + body — dùng cho NER (cung cấp context)."""
        path = " > ".join(self.heading_path())
        if path:
            return f"[CONTEXT: {path}]\n\n{self.body}"
        return self.body


# --- Markdown heading parser --------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def parse_markdown_tree(markdown: str) -> Section:
    """Parse Markdown → cây Section. Root là Section(level=0, title='')."""
    root = Section(level=0, title="")
    stack: list[Section] = [root]
    body_lines: list[str] = []

    def flush_body() -> None:
        if body_lines:
            stack[-1].body = "\n".join(body_lines).strip()
            body_lines.clear()

    for line in markdown.splitlines():
        m = _HEADING_RE.match(line)
        if not m:
            body_lines.append(line)
            continue

        flush_body()
        level = len(m.group(1))
        title = m.group(2).strip()
        while stack and stack[-1].level >= level:
            stack.pop()
        parent = stack[-1] if stack else root
        node = Section(level=level, title=title, parent=parent)
        parent.children.append(node)
        stack.append(node)

    flush_body()
    return root


# Heading patterns cần skip — language-agnostic (VN + EN).
# KHÔNG skip abstract/tóm tắt vì đó là chỗ entity dày nhất.
_SKIP_HEADING_PATTERNS = [
    re.compile(r"tài\s*liệu\s*tham\s*khảo|references?$", re.IGNORECASE),
    re.compile(r"mục\s*lục|table\s*of\s*contents", re.IGNORECASE),
    re.compile(r"lời\s*cảm\s*ơn|acknowledg", re.IGNORECASE),
    re.compile(r"phụ\s*lục|appendix", re.IGNORECASE),
]


def _is_noise_section(section: Section) -> bool:
    """Section references/mục lục/phụ lục → không trích entity. Hoạt động cả VN và EN."""
    for heading in section.heading_path():
        for pat in _SKIP_HEADING_PATTERNS:
            if pat.search(heading):
                return True
    return False


def iter_leaf_sections(root: Section) -> list[Section]:
    """Trả về các section có body, bỏ qua noise sections (references, mục lục, phụ lục)."""
    out: list[Section] = []
    if root.title and (root.body or not root.children):
        if not _is_noise_section(root):
            out.append(root)
    for child in root.children:
        out.extend(iter_leaf_sections(child))
    return out


# --- Topic detection từ heading -----------------------------------------

# Pattern đơn giản — rẻ hơn LLM, đủ cho phần lớn case y khoa tiếng Việt
_TOPIC_PATTERNS: list[tuple[re.Pattern, RelationType, str]] = [
    # "Điều trị tăng huyết áp" / "Phác đồ điều trị X"
    (re.compile(r"(?:điều\s*trị|phác\s*đồ|chữa)\s+(.+)$", re.IGNORECASE), RelationType.treats, "drug→disease"),
    # "Triệu chứng tăng huyết áp" / "Biểu hiện của X"
    (re.compile(r"(?:triệu\s*chứng|biểu\s*hiện|dấu\s*hiệu)\s+(?:của\s+|lâm\s*sàng\s+)?(.+)$", re.IGNORECASE), RelationType.has_symptom, "disease→symptom"),
    # "Tác dụng phụ của X" / "Tác dụng không mong muốn"
    (re.compile(r"(?:tác\s*dụng\s*phụ|tác\s*dụng\s*không\s*mong\s*muốn|phản\s*ứng\s*phụ)\s+(?:của\s+)?(.+)?$", re.IGNORECASE), RelationType.causes_se, "drug→symptom"),
]


def detect_topic(section: Section) -> tuple[RelationType, str] | None:
    """Phát hiện topic từ heading path. Trả (relation_type, topic_name) hoặc None."""
    for heading in reversed(section.heading_path()):
        for pattern, rel_type, _ in _TOPIC_PATTERNS:
            m = pattern.search(heading)
            if m:
                topic = (m.group(1) or "").strip().rstrip(".:;,") if m.lastindex else ""
                if topic or rel_type == RelationType.causes_se:
                    return rel_type, topic
    return None


# --- NER per section -----------------------------------------------------

def _ner_section(section: Section) -> dict:
    """NER hybrid (Gemini → Groq fallback) trên text section với context heading."""
    text = section.full_text()
    if not text.strip():
        return {"entities": [], "relationships": []}
    try:
        return _ner_via_gemini(text)
    except Exception as exc:
        if _is_quota_error(exc):
            logger.warning("Gemini NER quota → fallback Groq for section '%s'",
                           section.title[:50])
        else:
            logger.warning("Gemini NER failed for section '%s': %s",
                           section.title[:50], exc)
    try:
        return _ner_via_groq(text)
    except Exception as exc:
        logger.warning("Groq NER fallback also failed: %s", exc)
        return {"entities": [], "relationships": []}


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _coerce_entity_type(raw: str) -> EntityType | None:
    try:
        return EntityType(raw.upper())
    except (ValueError, AttributeError):
        return None


def _coerce_relation_type(raw: str) -> RelationType | None:
    try:
        return RelationType(raw.upper())
    except (ValueError, AttributeError):
        return None


# --- Section-aware extraction main loop ---------------------------------

def extract_with_structure(
    markdown: str, document_id: uuid.UUID
) -> tuple[list[MedicalEntity], list[Relationship], dict[uuid.UUID, list[str]]]:
    """
    Trả về (entities, relationships, entity_to_section_titles).
    entity_to_section_titles dùng cho audit + structural rel inference.
    Sentence-level NER + structural inference đều được merge.
    """
    root = parse_markdown_tree(markdown)
    sections = iter_leaf_sections(root)
    logger.info("Structural: %d section(s) parsed", len(sections))
    if not sections:
        sections = [Section(level=1, title="ROOT", body=markdown)]

    entity_by_norm: dict[str, MedicalEntity] = {}
    entity_section_map: dict[uuid.UUID, list[str]] = {}  # entity.id → list section titles
    relationships: list[Relationship] = []

    for sec in sections:
        result = _ner_section(sec)
        sec_entities_local: list[MedicalEntity] = []

        # 1. Sentence-level NER entities
        for raw in result.get("entities", []):
            name = (raw.get("name") or "").strip()
            norm = _normalize(raw.get("normalized_name") or name)
            etype = _coerce_entity_type(raw.get("type", ""))
            if not norm or not etype:
                continue
            ent = entity_by_norm.get(norm)
            if not ent:
                ent = MedicalEntity(
                    name=name or norm,
                    normalized_name=norm,
                    type=etype,
                    document_id=document_id,
                    description=raw.get("description"),
                )
                entity_by_norm[norm] = ent
            entity_section_map.setdefault(ent.id, []).append(sec.title or "")
            sec_entities_local.append(ent)

        # 2. Sentence-level NER relationships
        for raw_rel in result.get("relationships", []):
            src_norm = _normalize(raw_rel.get("source", ""))
            tgt_norm = _normalize(raw_rel.get("target", ""))
            rtype = _coerce_relation_type(raw_rel.get("type", ""))
            if not src_norm or not tgt_norm or not rtype:
                continue
            src = entity_by_norm.get(src_norm)
            tgt = entity_by_norm.get(tgt_norm)
            if not src or not tgt:
                continue
            relationships.append(Relationship(
                source_id=src.id,
                target_id=tgt.id,
                type=rtype,
                document_id=document_id,
                evidence=raw_rel.get("evidence"),
            ))

        # 3. Structural inference từ heading topic
        topic = detect_topic(sec)
        if not topic:
            continue
        rel_type, topic_name = topic
        topic_norm = _normalize(topic_name)

        # Tìm entity DISEASE khớp topic (qua normalized_name, dù chỉ partial)
        topic_disease = entity_by_norm.get(topic_norm)
        if not topic_disease and topic_norm:
            for e in entity_by_norm.values():
                if e.type == EntityType.disease and (topic_norm in e.normalized_name or e.normalized_name in topic_norm):
                    topic_disease = e
                    break

        # Suy luận
        evidence_text = f"Section '{' > '.join(sec.heading_path())}' liệt kê entity trong context '{rel_type.value}'"
        for ent in sec_entities_local:
            inferred: Relationship | None = None
            if rel_type == RelationType.treats and ent.type == EntityType.drug and topic_disease:
                inferred = Relationship(
                    source_id=ent.id, target_id=topic_disease.id,
                    type=RelationType.treats, document_id=document_id,
                    evidence=evidence_text, confidence=0.75,
                )
            elif rel_type == RelationType.has_symptom and ent.type == EntityType.symptom and topic_disease:
                inferred = Relationship(
                    source_id=topic_disease.id, target_id=ent.id,
                    type=RelationType.has_symptom, document_id=document_id,
                    evidence=evidence_text, confidence=0.75,
                )
            elif rel_type == RelationType.causes_se and ent.type == EntityType.symptom:
                # Tìm DRUG cùng section (topic_name có thể là drug name)
                for drug_ent in sec_entities_local:
                    if drug_ent.type != EntityType.drug:
                        continue
                    if topic_norm and topic_norm not in drug_ent.normalized_name and drug_ent.normalized_name not in topic_norm:
                        continue
                    inferred = Relationship(
                        source_id=drug_ent.id, target_id=ent.id,
                        type=RelationType.causes_se, document_id=document_id,
                        evidence=evidence_text, confidence=0.75,
                    )
                    break
            if inferred:
                relationships.append(inferred)

    # Dedupe relationships theo (source_id, target_id, type)
    seen: set[tuple] = set()
    unique_rels: list[Relationship] = []
    for r in relationships:
        key = (str(r.source_id), str(r.target_id), r.type.value)
        if key in seen:
            continue
        seen.add(key)
        unique_rels.append(r)

    logger.info(
        "Structural extract done: %d entities, %d rels (after dedup, before verify)",
        len(entity_by_norm), len(unique_rels),
    )
    return list(entity_by_norm.values()), unique_rels, entity_section_map
