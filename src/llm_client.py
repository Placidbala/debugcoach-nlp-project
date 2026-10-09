import os
import time

from openai import APIError, OpenAI


class LLMClient:
    """Thin wrapper around any OpenAI-compatible chat API."""

    def __init__(self, cfg: dict):
        key = os.getenv(cfg["api_key_env"])
        if not key:
            raise RuntimeError(
                f"Missing API key. Set {cfg['api_key_env']} in your .env file."
            )
        self.cfg = cfg
        self.client = OpenAI(
            api_key=key, base_url=cfg["base_url"], timeout=cfg.get("timeout_s", 30)
        )

    def complete(self, system: str, user: str) -> str:
        kwargs = dict(
            model=self.cfg["model"],
            temperature=self.cfg.get("temperature", 0.2),
            max_tokens=self.cfg.get("max_tokens", 800),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if self.cfg.get("json_mode"):
            kwargs["response_format"] = {"type": "json_object"}

        retries = self.cfg.get("max_retries", 2)
        for attempt in range(retries + 1):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except APIError:
                if attempt == retries:
                    raise
                time.sleep(2 ** attempt)  # exponential backoff
