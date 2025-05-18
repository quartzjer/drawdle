import os
from typing import AsyncIterator, Callable, Dict

from anthropic import AsyncAnthropic
from google import genai
from google.genai import types
from openai import AsyncOpenAI


class ModelStreamer:
    """Encapsulate streaming logic for supported AI models."""

    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self.client_anthropic = AsyncAnthropic()
        self.client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.client_openai = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        self._dispatch: Dict[str, Callable[[str], AsyncIterator[str]]] = {
            "claude": self.stream_claude,
            "gemini": self.stream_gemini,
            "openai": self.stream_openai,
        }

    async def stream_claude(self, prompt: str) -> AsyncIterator[str]:
        """Yield text chunks from Claude."""
        async with self.client_anthropic.messages.stream(
            max_tokens=1024,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            model="claude-3-7-sonnet-20250219",
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def stream_gemini(self, prompt: str) -> AsyncIterator[str]:
        """Yield text chunks from Gemini."""
        async for chunk in self.client_gemini.aio.models.generate_content_stream(
            model="gemini-2.0-pro-exp-02-05",
            contents=[types.Part.from_text(prompt)],
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                max_output_tokens=1024,
            ),
        ):
            yield chunk

    async def stream_openai(self, prompt: str) -> AsyncIterator[str]:
        """Yield text chunks from OpenAI."""
        response = await self.client_openai.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}],
                },
                {"role": "user", "content": [{"type": "text", "text": prompt}]},
            ],
            model="o3-mini",
            reasoning_effort="low",
            stream=True,
        )
        async for chunk in response:
            yield chunk

    def get_streamer(self, model_name: str) -> Callable[[str], AsyncIterator[str]]:
        """Return streaming function for the requested model."""
        return self._dispatch.get(model_name.lower(), self.stream_claude)

