import os
from openai import OpenAI


class LLMService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-mini"

    def chat(self, prompt: str, max_tokens: int = 256) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content
