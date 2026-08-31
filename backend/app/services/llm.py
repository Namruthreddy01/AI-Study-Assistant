import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import GenerationError


class LlmProvider(ABC):
    """Boundary around the model provider; routes never know a provider name."""

    @abstractmethod
    async def answer(self, question: str, context: str) -> str:
        """Answer using the supplied study context only."""

    @abstractmethod
    async def generate_json(self, task: str, context: str, instruction: str) -> dict[str, Any]:
        """Generate a JSON object matching an instruction."""


class OpenAICompatibleProvider(LlmProvider):
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.ai_api_key
        self.base_url = settings.ai_base_url.rstrip("/")
        self.model = settings.llm_model

    async def _completion(self, system: str, user: str, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise GenerationError("The AI service is unavailable. Please try again.") from error
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise GenerationError("The AI service returned an invalid response.") from error

    async def answer(self, question: str, context: str) -> str:
        system = (
            "You are an AI Study Assistant. Answer only from the supplied material. "
            "If the material is insufficient, say exactly that it was not found in the uploaded material. "
            "Be concise and helpful. Do not invent facts."
        )
        return await self._completion(system, f"Question: {question}\n\nMaterial:\n{context}")

    async def generate_json(self, task: str, context: str, instruction: str) -> dict[str, Any]:
        system = (
            "You create study resources only from the supplied material. "
            "Return valid JSON only, matching the requested shape. Never add markdown."
        )
        content = await self._completion(
            system,
            f"Task: {task}\nInstruction: {instruction}\n\nMaterial:\n{context}",
            json_mode=True,
        )
        try:
            result = json.loads(content)
        except json.JSONDecodeError as error:
            raise GenerationError("The AI service returned malformed study content.") from error
        if not isinstance(result, dict):
            raise GenerationError("The AI service returned invalid study content.")
        return result


class OfflineStudyProvider(LlmProvider):
    """Grounded fallback so the app remains demoable without an API key."""

    @staticmethod
    def _sentences(context: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", context.replace("\n", " "))
        return [sentence.strip() for sentence in sentences if len(sentence.strip()) > 25]

    async def answer(self, question: str, context: str) -> str:
        question_words = set(re.findall(r"[a-zA-Z0-9]{3,}", question.lower()))
        candidates = self._sentences(context)
        scored = [
            (
                len(question_words.intersection(set(re.findall(r"[a-zA-Z0-9]{3,}", sentence.lower())))),
                sentence,
            )
            for sentence in candidates
        ]
        selected = [sentence for score, sentence in sorted(scored, reverse=True) if score > 0][:3]
        if not selected:
            return "I couldn't find enough information about this topic in the uploaded material."
        return "Based on the uploaded material: " + " ".join(selected)

    async def generate_json(self, task: str, context: str, instruction: str) -> dict[str, Any]:
        sentences = self._sentences(context)
        if task == "summary":
            points = sentences[:8]
            return {
                "overview": " ".join(points[:3]) or "The document contains study material.",
                "key_points": points[:5],
                "important_concepts": [sentence[:120].rstrip(" .") for sentence in points[:5]],
                "exam_focus": points[-3:] if points else [],
            }
        return {}


def create_llm_provider(settings: Settings) -> LlmProvider:
    return OpenAICompatibleProvider(settings) if settings.ai_api_key else OfflineStudyProvider()

