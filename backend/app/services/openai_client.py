from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.core.config import Settings


@dataclass
class OpenAIClient:
    client: OpenAI
    embedding_model: str
    completion_model: str

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenAIClient":
        client = OpenAI(api_key=settings.openai_api_key)
        return cls(
            client=client,
            embedding_model=settings.embedding_model,
            completion_model=settings.completion_model,
        )

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(input=text, model=self.embedding_model)
        return response.data[0].embedding  # type: ignore[attr-defined]

    def chat(self, prompt: str, temperature: float = 0.1) -> str:
        response: Any = self.client.chat.completions.create(
            model=self.completion_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content  # type: ignore[index]

    def stream_chat(self, prompt: str, temperature: float = 0.1):
        stream = self.client.chat.completions.create(
            model=self.completion_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content  # type: ignore[index]
            if delta:
                yield delta
