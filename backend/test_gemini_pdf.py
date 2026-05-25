"""
Test cụ thể: Gemini PDF upload có hoạt động không?
Chạy: python test_gemini_pdf.py <path_to_pdf>
"""
import sys
import pathlib

sys.path.insert(0, ".")
import google.generativeai as genai
from src.mkge.config import settings


def test_inline(pdf_path: str):
    print("--- Test 1: Inline PDF bytes (current method) ---")
    genai.configure(api_key=settings.gemini_api_key)
    pdf_bytes = pathlib.Path(pdf_path).read_bytes()
    print(f"PDF size: {len(pdf_bytes)} bytes")
    model = genai.GenerativeModel(settings.gemini_parsing_model)
    try:
        r = model.generate_content(
            [{"mime_type": "application/pdf", "data": pdf_bytes}, "Tóm tắt nội dung."],
            request_options={"timeout": 30},
        )
        print(f"OK: {r.text[:200]}")
    except Exception as e:
        print(f"FAIL inline: {e}")


def test_files_api(pdf_path: str):
    print("\n--- Test 2: Files API upload (alternative) ---")
    genai.configure(api_key=settings.gemini_api_key)
    try:
        f = genai.upload_file(path=pdf_path)
        print(f"Uploaded: {f.name}, uri={f.uri}")
        model = genai.GenerativeModel(settings.gemini_parsing_model)
        r = model.generate_content(
            [f, "Tóm tắt nội dung."],
            request_options={"timeout": 30},
        )
        print(f"OK: {r.text[:200]}")
    except Exception as e:
        print(f"FAIL files-api: {e}")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    if not pdf or not pathlib.Path(pdf).exists():
        print("Usage: python test_gemini_pdf.py <pdf_file>")
        print("Tip: dùng PDF nhỏ (1-2 trang) để test nhanh")
        sys.exit(1)
    test_inline(pdf)
    test_files_api(pdf)
