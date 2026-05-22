"""
Stage 1: Structural Parsing.
Outputs:
  - markdown: Gemini Flash → Markdown structured (PROJECT_CONTEXT §9 step 1).
    Dùng cho Stage 4 (heading tree, topic detection).
  - chunks: page-aware Chunk objects (PROJECT_CONTEXT §4.2).
    Dùng cho Stage 2 NER + Stage 3 embedding + citation tracking.

Markdown lấy từ Gemini (fallback pdfplumber khi 429).
Page mapping luôn lấy từ pdfplumber vì Gemini không emit trang.
"""
import logging
import pathlib
import uuid

import google.generativeai as genai
import pdfplumber
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from src.mkge.config import settings
from src.mkge.domain.entities.chunk import Chunk

logger = logging.getLogger(__name__)


_MARKDOWN_PROMPT = """Bạn là chuyên gia phân tích cấu trúc văn bản y khoa.
Nhiệm vụ: đọc PDF y khoa tiếng Việt, chuyển toàn bộ nội dung sang Markdown chuẩn.

YÊU CẦU:
1. Giữ NGUYÊN cấu trúc heading (# ## ###), danh sách (- *), bảng (| col | col |), đoạn văn
2. Giữ NGUYÊN tên thuốc, tên bệnh, liều lượng, đơn vị, ký hiệu y học
3. KHÔNG tóm tắt, KHÔNG diễn giải, KHÔNG thêm comment
4. Bỏ header/footer trang, số trang, watermark
5. Nếu có bảng, dùng cú pháp Markdown table

OUTPUT: CHỈ Markdown thuần, KHÔNG fence ```markdown ```, KHÔNG lời giải thích.
"""


_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


# --- Gemini parsing -------------------------------------------------------

def _configure_gemini() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=settings.gemini_api_key)


def _gemini_pdf_to_markdown(file_path: str, timeout: int = 60) -> str:
    _configure_gemini()
    pdf_bytes = pathlib.Path(file_path).read_bytes()
    model = genai.GenerativeModel(
        settings.gemini_parsing_model,
        system_instruction=_MARKDOWN_PROMPT,
        generation_config={"temperature": 0.0, "max_output_tokens": 65536},
        safety_settings=_SAFETY_SETTINGS,
    )
    # Timeout cứng để pipeline không bị treo nếu Gemini không phản hồi
    response = model.generate_content(
        [{"mime_type": "application/pdf", "data": pdf_bytes}, "Chuyển PDF này sang Markdown."],
        request_options={"timeout": timeout},
    )
    if not response.candidates:
        raise RuntimeError(f"Gemini parsing returned no candidates: {response.prompt_feedback}")
    parts = response.candidates[0].content.parts
    if not parts:
        raise RuntimeError("Gemini parsing returned empty content")
    return "".join(p.text for p in parts if hasattr(p, "text")).strip()


# --- pdfplumber page extraction ------------------------------------------

def _extract_pages(file_path: str) -> list[tuple[int, str]]:
    """Page-by-page raw text (1-indexed). Skip empty pages."""
    out: list[tuple[int, str]] = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text(x_tolerance=2) or "").strip()
            if text:
                out.append((i, text))
    return out


def _pages_to_markdown(pages: list[tuple[int, str]], max_chars: int) -> str:
    """Fallback markdown khi Gemini không có. Mỗi page là 1 section."""
    parts = []
    total = 0
    for page_num, text in pages:
        chunk = f"## Trang {page_num}\n\n{text}\n"
        parts.append(chunk)
        total += len(chunk)
        if total >= max_chars:
            break
    return "\n".join(parts)[:max_chars]


# --- Chunking ------------------------------------------------------------

def _split_page_text(
    page_num: int,
    text: str,
    document_id: uuid.UUID,
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    """Split 1 page thành nhiều Chunk nếu page > chunk_size."""
    if len(text) <= chunk_size:
        return [Chunk(document_id=document_id, page=page_num, text=text)]
    out: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        out.append(Chunk(document_id=document_id, page=page_num, text=text[start:end]))
        if end >= len(text):
            break
        start = end - overlap
    return out


def build_chunks(
    pages: list[tuple[int, str]],
    document_id: uuid.UUID,
    *,
    chunk_size: int = 4000,
    overlap: int = 400,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page_num, text in pages:
        chunks.extend(_split_page_text(page_num, text, document_id, chunk_size, overlap))
    return chunks


# --- Public API ----------------------------------------------------------

def parse_document(
    file_path: str,
    document_id: uuid.UUID,
    *,
    max_markdown_chars: int = 250_000,
) -> tuple[str, list[Chunk]]:
    """
    Stage 1 chính:
      → (markdown_text, list[Chunk])

    markdown_text dùng cho Stage 4 (heading tree).
    chunks dùng cho Stage 2 NER + Stage 3 embedding.
    """
    pages = _extract_pages(file_path)
    logger.info("pdfplumber: %d page(s) with text", len(pages))

    # Markdown (cho Stage 4)
    try:
        markdown = _gemini_pdf_to_markdown(file_path)
        logger.info("Gemini → markdown len=%d", len(markdown))
    except Exception as exc:
        logger.warning("Gemini parsing failed (%s) → fallback markdown từ pages", exc)
        markdown = _pages_to_markdown(pages, max_markdown_chars)
    markdown = markdown[:max_markdown_chars]

    # Chunks page-aware (cho citation + embedding)
    chunks = build_chunks(pages, document_id)
    logger.info("Built %d chunk(s) from %d pages", len(chunks), len(pages))

    return markdown, chunks


# --- Backward-compat ----------------------------------------------------

def extract_text(file_path: str, max_chars: int = 250_000) -> str:
    """Backward-compat: chỉ trả markdown, không trả chunks."""
    pages = _extract_pages(file_path)
    try:
        md = _gemini_pdf_to_markdown(file_path)
    except Exception as exc:
        logger.warning("Gemini parsing failed (%s) → fallback pages markdown", exc)
        md = _pages_to_markdown(pages, max_chars)
    return md[:max_chars]


def chunk_text(text: str, chunk_size: int = 8000, overlap: int = 400) -> list[str]:
    """Backward-compat: dùng cho service._extract_raw_graph cũ."""
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks
