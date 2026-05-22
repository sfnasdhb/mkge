"""
LLM Generator for GraphRAG Query Response using Gemini.
"""
import logging
import google.generativeai as genai

from src.mkge.config import settings

logger = logging.getLogger(__name__)

def _configure() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=settings.gemini_api_key)

def generate_graphrag_answer(query: str, context_text: str) -> str:
    _configure()
    
    prompt = f"""
You are an expert medical assistant.
Answer the user's question based strictly on the provided Context.
If the context does not contain enough information to answer the question, state that you don't know based on the provided documents. Do not hallucinate or use external knowledge.

Context:
{context_text}

User Question:
{query}

Answer:
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating answer with Gemini: {e}")
        return "I encountered an error while trying to generate the answer."
