from abc import ABC, abstractmethod
from typing import Generator
import os
import openai
import anthropic


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        ...

    @abstractmethod
    def chat_stream(self, messages: list[dict], system_prompt: str | None = None) -> Generator[str, None, None]:
        ...


class OpenAIClient(LLMClient):
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        response = self.client.chat.completions.create(model=self.model, messages=full_messages)
        return response.choices[0].message.content or ""

    def chat_stream(self, messages: list[dict], system_prompt: str | None = None) -> Generator[str, None, None]:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        with self.client.chat.completions.create(model=self.model, messages=full_messages, stream=True) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta


class AnthropicClient(LLMClient):
    def __init__(self, model: str = "claude-3-5-haiku-20241022"):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        kwargs = {"model": self.model, "max_tokens": 2048, "messages": messages}
        if system_prompt:
            kwargs["system"] = system_prompt
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def chat_stream(self, messages: list[dict], system_prompt: str | None = None) -> Generator[str, None, None]:
        kwargs = {"model": self.model, "max_tokens": 2048, "messages": messages}
        if system_prompt:
            kwargs["system"] = system_prompt
        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text


def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL")
    if provider == "anthropic":
        return AnthropicClient(model=model or "claude-3-5-haiku-20241022")
    return OpenAIClient(model=model or "gpt-4o-mini")
