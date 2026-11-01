"""
Configurable Schema-Aware LLM SQL Generator (Approach 2).
Supports Google Gemini, OpenAI-compatible APIs, and automatic offline fallback to baseline.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional
import requests

from config.settings import LLMSettings, get_settings
from database.schema_detector import DatabaseSchema
from generation.baseline_generator import BaselineSQLGenerator
from generation.prompt_builder import PromptBuilder
from generation.response_parser import ParsedLLMResponse, ResponseParser

logger = logging.getLogger(__name__)


@dataclass
class LLMGenerationResult:
    sql: str
    explanation: str
    tables_used: list[str]
    columns_used: list[str]
    assumptions: list[str]
    needs_clarification: bool
    generation_time_ms: float
    provider: str
    raw_response: str = ""
    approach: str = "Schema-Aware LLM Generation"


class LLMGenerator:
    """Manages schema-aware LLM query generation with multi-provider and offline fallback support."""

    def __init__(self, schema: DatabaseSchema, settings: Optional[LLMSettings] = None):
        self.schema = schema
        self.settings = settings or get_settings().llm
        self.prompt_builder = PromptBuilder(schema)
        self.baseline_fallback = BaselineSQLGenerator(schema)

    def generate(
        self,
        question: str,
        conversation_history: Optional[list[dict[str, str]]] = None,
        force_provider: Optional[str] = None
    ) -> LLMGenerationResult:
        provider = (force_provider or self.settings.provider).lower()
        start_time = time.perf_counter()

        # Handle offline or unconfigured mode
        if provider == "offline" or (provider == "gemini" and not self.settings.gemini_api_key) or (provider == "openai" and not self.settings.openai_api_key):
            logger.info(f"Using baseline fallback (provider={provider}, api_key configured={bool(self.settings.gemini_api_key or self.settings.openai_api_key)})")
            base_res = self.baseline_fallback.generate(question)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return LLMGenerationResult(
                sql=base_res.sql,
                explanation=base_res.explanation,
                tables_used=base_res.linked_tables,
                columns_used=base_res.linked_columns,
                assumptions=["No external LLM API key detected; executed via Traditional NLP Baseline."],
                needs_clarification=False,
                generation_time_ms=elapsed_ms,
                provider="offline-baseline"
            )

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(question, conversation_history)

        try:
            if provider == "gemini":
                raw_reply = self._call_gemini(system_prompt, user_prompt)
            elif provider == "openai":
                raw_reply = self._call_openai(system_prompt, user_prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

            parsed = ResponseParser.parse(raw_reply)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return LLMGenerationResult(
                sql=parsed.sql,
                explanation=parsed.explanation,
                tables_used=parsed.tables_used,
                columns_used=parsed.columns_used,
                assumptions=parsed.assumptions,
                needs_clarification=parsed.needs_clarification,
                generation_time_ms=elapsed_ms,
                provider=provider,
                raw_response=raw_reply
            )

        except Exception as e:
            logger.error(f"LLM API call failed ({e}), invoking baseline fallback...")
            base_res = self.baseline_fallback.generate(question)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return LLMGenerationResult(
                sql=base_res.sql,
                explanation=base_res.explanation,
                tables_used=base_res.linked_tables,
                columns_used=base_res.linked_columns,
                assumptions=[f"LLM API error ({e}); gracefully fell back to Traditional Baseline."],
                needs_clarification=False,
                generation_time_ms=elapsed_ms,
                provider="offline-baseline-fallback"
            )

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Invokes Google Gemini API via official v1beta REST endpoint."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent?key={self.settings.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Invokes OpenAI-compatible chat completion endpoint."""
        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.settings.openai_model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

