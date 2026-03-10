"""
Gemini LLM Integration — Decision layer for agents.
Uses Google Gemini API for intelligent decision-making.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini(prompt: str, system_instruction: str = "", temperature: float = 0.3,
                max_tokens: int = 1024) -> Optional[str]:
    """Call Gemini API and return the text response."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — using fallback logic")
        return None

    try:
        url = f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        contents = [{"parts": [{"text": prompt}]}]
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        response = requests.post(url, json=body, timeout=30)
        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")

        return None

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None


def ask_gemini_json(prompt: str, system_instruction: str = "") -> Optional[Dict[str, Any]]:
    """Call Gemini and parse JSON response."""
    json_prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
    text = call_gemini(json_prompt, system_instruction)
    if not text:
        return None

    # Clean up common issues
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON: {e}\nRaw: {text[:500]}")
        return None
