"""
LLM Generator for GraphRAG Query Response using Gemini.
"""
import logging
import google.generativeai as genai

from src.mkge.config import settings

logger = logging.getLogger(__name__)

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=settings.gemini_api_key)
    _configured = True


def generate_graphrag_answer(query: str, context_text: str, temperature: float | None = None) -> str:
    _configure()

    prompt = f"""You are an expert medical assistant.
Answer the user's question based strictly on the provided Context.
If the context does not contain enough information to answer the question, state that you don't know based on the provided documents. Do not hallucinate or use external knowledge.
Answer in the same language as the user's question (Vietnamese if question is in Vietnamese).

Context:
{context_text}

User Question:
{query}

Answer:"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        gen_config = {}
        if temperature is not None:
            gen_config["temperature"] = temperature

        response = model.generate_content(
            prompt,
            generation_config=gen_config if gen_config else None,
            request_options={"timeout": 120},
        )
        answer = response.text.strip()
        logger.info("Gemini answer generated (%d chars)", len(answer))
        return answer
    except Exception as e:
        logger.error("Error generating answer with Gemini: %s", e, exc_info=True)
        return "Đã xảy ra lỗi khi tạo câu trả lời. Vui lòng thử lại sau."

