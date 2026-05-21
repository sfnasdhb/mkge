"""
Stage 3: Dual-model verification.
NER ở Stage 2 đã trích relationships (Gemini primary, Groq fallback — recall-oriented).
Llama 4 (Groq) đánh giá lại từng relationship dựa trên evidence để tăng precision.

Output: list relationships đã verified với confidence được cập nhật.
Relationships có confidence < threshold sẽ bị loại trước khi ghi Neo4j.

Lưu ý: khi Stage 2 cũng phải fallback sang Groq (Gemini 429), Stage 3 vẫn dùng Groq
→ mất tính dual-model khách quan. Đây là đánh đổi để pipeline không gãy.
"""
import json
import logging
import re
from typing import Sequence

from groq import Groq

from src.mkge.config import settings
from src.mkge.domain.entities.graph import MedicalEntity, Relationship

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """Bạn là chuyên gia y khoa đánh giá tính đúng đắn của các mối quan hệ lâm sàng.

Với mỗi RELATIONSHIP gồm (source_entity, relation_type, target_entity, evidence_text),
hãy đánh giá:
- verified=true: evidence_text TRỰC TIẾP hỗ trợ relation_type giữa source và target
- verified=false: evidence_text không hỗ trợ, hoặc relation_type sai, hoặc suy diễn quá xa

CONFIDENCE (0.0-1.0):
- 0.9-1.0: evidence nêu rõ ràng, không nghi ngờ
- 0.6-0.8: evidence ngụ ý mạnh nhưng không tường minh
- 0.3-0.5: evidence ngụ ý yếu, có thể đúng nhưng không chắc
- 0.0-0.2: evidence không liên quan hoặc mâu thuẫn

LOẠI QUAN HỆ (CHỈ 4 loại):
- TREATS: Thuốc điều trị Bệnh (DRUG → DISEASE)
- CAUSES_SE: Thuốc gây tác dụng phụ là Triệu chứng (DRUG → SYMPTOM)
- HAS_SYMPTOM: Bệnh có triệu chứng (DISEASE → SYMPTOM)
- COMORBID: Bệnh đồng mắc với Bệnh khác (DISEASE → DISEASE)

INPUT: JSON array các relationship.
OUTPUT: JSON object {"results": [{"index": 0, "verified": true/false, "confidence": 0.0-1.0, "reason": "ngắn gọn"}, ...]}
CHỈ trả JSON, KHÔNG markdown fence, KHÔNG giải thích thêm.
"""


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _build_batch_payload(
    relationships: Sequence[Relationship],
    entity_by_id: dict,
) -> list[dict]:
    payload = []
    for i, rel in enumerate(relationships):
        src = entity_by_id.get(rel.source_id)
        tgt = entity_by_id.get(rel.target_id)
        if not src or not tgt:
            continue
        payload.append({
            "index": i,
            "source_entity": f"{src.name} ({src.type.value})",
            "relation_type": rel.type.value,
            "target_entity": f"{tgt.name} ({tgt.type.value})",
            "evidence_text": rel.evidence or "(không có evidence)",
        })
    return payload


def _verify_batch(
    client: Groq,
    batch: list[dict],
    model_name: str,
) -> dict[int, tuple[bool, float, str]]:
    """Gọi Groq verify 1 batch. Trả mapping {original_index: (verified, confidence, reason)}."""
    user_msg = json.dumps(batch, ensure_ascii=False, indent=2)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4096,
        )
    except Exception as exc:
        logger.warning("Groq verify batch failed: %s — assume all verified=true conf=0.5", exc)
        return {item["index"]: (True, 0.5, "verifier_failed") for item in batch}

    raw = response.choices[0].message.content or ""
    try:
        data = _parse_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Verifier JSON parse failed: %s | raw=%r", exc, raw[:300])
        return {item["index"]: (True, 0.5, "parse_failed") for item in batch}

    results: dict[int, tuple[bool, float, str]] = {}
    for r in data.get("results", []):
        idx = r.get("index")
        if not isinstance(idx, int):
            continue
        verified = bool(r.get("verified", False))
        try:
            confidence = float(r.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        reason = str(r.get("reason", ""))[:200]
        results[idx] = (verified, confidence, reason)
    return results


def verify_relationships(
    entities: Sequence[MedicalEntity],
    relationships: Sequence[Relationship],
    *,
    batch_size: int = 8,
    threshold: float | None = None,
    model_name: str | None = None,
) -> list[Relationship]:
    """
    Verify từng relationship qua Groq Llama. Trả về list relationships
    có verified=True và confidence >= threshold. Confidence được cập nhật từ verifier.
    """
    if not relationships:
        return []
    if not settings.groq_api_key or settings.groq_api_key == "xxxx":
        logger.warning("GROQ_API_KEY not set — skipping verification, returning all relationships as-is")
        return list(relationships)

    threshold = threshold if threshold is not None else settings.verification_threshold
    model = model_name or settings.groq_verifier_model
    entity_by_id = {e.id: e for e in entities}
    client = Groq(api_key=settings.groq_api_key)

    rel_list = list(relationships)
    payload = _build_batch_payload(rel_list, entity_by_id)
    if not payload:
        return []

    verdicts: dict[int, tuple[bool, float, str]] = {}
    for start in range(0, len(payload), batch_size):
        batch = payload[start : start + batch_size]
        batch_verdicts = _verify_batch(client, batch, model)
        verdicts.update(batch_verdicts)
        logger.info(
            "Verifier batch %d-%d: %d/%d verified",
            start,
            start + len(batch) - 1,
            sum(1 for v, _, _ in batch_verdicts.values() if v),
            len(batch),
        )

    kept: list[Relationship] = []
    rejected = 0
    for i, rel in enumerate(rel_list):
        v = verdicts.get(i)
        if v is None:
            kept.append(rel)
            continue
        verified, confidence, reason = v
        if not verified or confidence < threshold:
            rejected += 1
            logger.info(
                "REJECT rel %s (verified=%s conf=%.2f reason=%s)",
                rel.type.value, verified, confidence, reason,
            )
            continue
        kept.append(rel.model_copy(update={"confidence": confidence}))

    logger.info(
        "Verification done: kept %d / rejected %d / total %d (threshold=%.2f)",
        len(kept), rejected, len(rel_list), threshold,
    )
    return kept
