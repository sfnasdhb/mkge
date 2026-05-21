"""
Stage 2: Named Entity Recognition + Relationship Extraction.
Theo kế hoạch: Gemini làm primary NER.
Fallback: Groq Llama khi Gemini 429 / lỗi khác (để pipeline không gãy khi quota cạn).
"""
import json
import logging
import re

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from groq import Groq

from src.mkge.config import settings

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """Bạn là chuyên gia trích xuất tri thức y khoa từ văn bản tiếng Việt.
Nhiệm vụ: từ đoạn văn bản y khoa, trích xuất các thực thể và quan hệ.

CÁC LOẠI THỰC THỂ (CHỈ 3 loại — không thêm loại khác):
- DRUG: tên thuốc, hoạt chất (vd: Paracetamol, Amoxicillin, Enalapril). Vacxin cũng tính DRUG.
- DISEASE: tên bệnh, chẩn đoán, biến chứng (vd: Viêm phổi, Tăng huyết áp, Đái tháo đường type 2)
- SYMPTOM: triệu chứng lâm sàng MÀ BỆNH NHÂN CẢM NHẬN ĐƯỢC hoặc khám LÂM SÀNG thấy (vd: Sốt, Đau đầu, Khó thở, Phù chân, Ho khan)

KHÔNG TRÍCH các loại sau (DÙ XUẤT HIỆN NHIỀU LẦN):
- Xét nghiệm cận lâm sàng (xét nghiệm máu, X-quang, ECG, siêu âm, nội soi, MRI, CT scan...)
- Thủ thuật / phẫu thuật (đặt stent, mổ, sinh thiết...)
- Chỉ số lab (HbA1c, LDL, creatinine, bạch cầu tăng...) — đây là kết quả test, không phải triệu chứng
- Tên bài báo / tác giả trong references
- Đơn vị đo (mmHg, mg, mL...)
- Khái niệm chung (yếu tố nguy cơ, biến chứng, chỉ định...) trừ khi là tên bệnh cụ thể

CÁC LOẠI QUAN HỆ (CHỈ 4 loại):
- TREATS: Thuốc điều trị Bệnh (source=DRUG, target=DISEASE)
- CAUSES_SE: Thuốc gây tác dụng phụ là Triệu chứng (source=DRUG, target=SYMPTOM)
- HAS_SYMPTOM: Bệnh có triệu chứng (source=DISEASE, target=SYMPTOM)
- COMORBID: Bệnh đồng mắc với Bệnh khác (source=DISEASE, target=DISEASE)

QUY TẮC:
1. Chuẩn hoá tên: viết thường, BỎ DẤU phụ tiếng Việt, chuẩn hoá khoảng trắng → normalized_name
2. Giữ name gốc (có dấu, đúng chính tả)
3. Mỗi entity duy nhất theo normalized_name; không tạo trùng
4. Chỉ trích quan hệ có CĂN CỨ TRỰC TIẾP trong văn bản
5. Trả về CHÍNH XÁC JSON theo schema, KHÔNG markdown fence, KHÔNG giải thích

SCHEMA OUTPUT:
{
  "entities": [
    {"name": "...", "normalized_name": "...", "type": "DRUG|DISEASE|SYMPTOM", "description": "..."}
  ],
  "relationships": [
    {"source": "<normalized_name>", "target": "<normalized_name>", "type": "TREATS|CAUSES_SE|HAS_SYMPTOM|COMORBID", "evidence": "trích đoạn ngắn"}
  ]
}
"""


_GEMINI_SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _gemini_extract_text(response) -> str | None:
    """Safely pull text from Gemini response."""
    try:
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning("Gemini BLOCKED prompt: %s", response.prompt_feedback)
            return None
    except Exception:
        pass
    if not response.candidates:
        return None
    try:
        parts = response.candidates[0].content.parts
        if not parts:
            return None
        return "".join(p.text for p in parts if hasattr(p, "text"))
    except Exception:
        return None


def _ner_via_gemini(text: str) -> dict:
    """Primary NER path — Gemini. Raises ResourceExhausted on 429, propagates other errors."""
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        settings.gemini_ner_model,
        system_instruction=_SYSTEM_PROMPT,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "max_output_tokens": 8192,
        },
        safety_settings=_GEMINI_SAFETY,
    )
    response = model.generate_content(
        f"VĂN BẢN:\n{text}",
        request_options={"timeout": 30},
    )
    raw = _gemini_extract_text(response)
    if not raw:
        logger.warning("Gemini NER empty response")
        return {"entities": [], "relationships": []}
    logger.info("Gemini NER raw (first 200 chars): %s", raw[:200])
    return _parse_json(raw)


def _ner_via_groq(text: str) -> dict:
    """Fallback NER path — Groq Llama."""
    if not settings.groq_api_key or settings.groq_api_key == "xxxx":
        raise RuntimeError("GROQ_API_KEY is not configured (cannot fall back)")
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_verifier_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"VĂN BẢN:\n{text}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=8192,
    )
    raw = response.choices[0].message.content or ""
    if not raw:
        return {"entities": [], "relationships": []}
    logger.info("Groq NER raw (first 200 chars): %s", raw[:200])
    return _parse_json(raw)


def _is_quota_error(exc: Exception) -> bool:
    """Detect quota / rate limit errors from Gemini."""
    if isinstance(exc, ResourceExhausted):
        return True
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "rate limit" in msg or "resource_exhausted" in msg


def extract_entities_and_relations(text: str, model_name: str | None = None) -> dict:
    """
    Hybrid NER: Gemini primary, Groq fallback on 429/quota errors.
    Trả {"entities": [...], "relationships": [...]}. Không bao giờ raise.
    """
    try:
        data = _ner_via_gemini(text)
        return {
            "entities": data.get("entities", []),
            "relationships": data.get("relationships", []),
        }
    except Exception as exc:
        if _is_quota_error(exc):
            logger.warning("Gemini NER quota exhausted → fallback Groq")
        else:
            logger.warning("Gemini NER failed (%s) → fallback Groq", exc)

    try:
        data = _ner_via_groq(text)
        return {
            "entities": data.get("entities", []),
            "relationships": data.get("relationships", []),
        }
    except Exception as exc:
        logger.warning("Groq NER fallback also failed: %s", exc)
        return {"entities": [], "relationships": []}
