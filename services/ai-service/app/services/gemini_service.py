"""
Upgraded Gemini Service — supports multi-turn tool calling for agentic loops.
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

import requests


def _post_gemini(payload: Dict, timeout: int = 60) -> Optional[Dict]:
    """Raw Gemini API call with retry."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — AI features disabled")
        return None
    url = f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Gemini attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return None


def call_gemini(prompt: str, system_instruction: str = "", temperature: float = 0.3,
                max_tokens: int = 2048) -> Optional[str]:
    """Simple text generation."""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    data = _post_gemini(body)
    if not data:
        return None
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def ask_gemini_json(prompt: str, system_instruction: str = "") -> Optional[Dict[str, Any]]:
    """Call Gemini and parse JSON response."""
    text = call_gemini(
        prompt + "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation.",
        system_instruction, temperature=0.2
    )
    if not text:
        return None
    text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Gemini JSON parse failed: {e}\nRaw: {text[:500]}")
        return None


def call_gemini_with_tools(prompt: str, tools_schema: List[Dict],
                            system_instruction: str = "",
                            conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Gemini call that supports function calling schema.
    Returns: {"type": "text", "text": "..."} or {"type": "tool_call", "name": "...", "params": {...}}
    """
    contents = []
    if conversation_history:
        contents.extend(conversation_history)
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    body = {
        "contents": contents,
        "tools": [{"functionDeclarations": tools_schema}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    data = _post_gemini(body)
    if not data:
        return {"type": "text", "text": "Unable to process request — AI service unavailable"}

    try:
        candidate = data["candidates"][0]
        parts = candidate["content"]["parts"]
        for part in parts:
            if "functionCall" in part:
                fn = part["functionCall"]
                return {"type": "tool_call", "name": fn["name"], "params": fn.get("args", {})}
            if "text" in part:
                return {"type": "text", "text": part["text"]}
    except Exception as e:
        logger.error(f"Gemini response parse error: {e}\nData: {str(data)[:500]}")

    return {"type": "text", "text": "Unable to parse AI response"}


def count_tokens(text: str) -> int:
    """Rough token estimation (4 chars ≈ 1 token)."""
    return len(text) // 4
