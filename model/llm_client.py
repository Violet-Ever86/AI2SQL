import json
import requests
from typing import Dict


class LLMClient:
    """LLM客户端类，负责与LLM API交互"""

    def __init__(self, endpoint: str, model: str, api_key: str = "", api_type: str = "completion"):
        """
        api_type:
          - "completion": OpenAI /v1/completions （payload 使用 prompt）
          - "chat": OpenAI /v1/chat/completions （payload 使用 messages）
        """
        self.base_endpoint = endpoint.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.api_type = api_type

    def _url(self) -> str:
        """构建API URL"""
        # 如果用户给了完整路径就用之，否则补默认路径
        if self.base_endpoint.endswith("/v1/completions") or self.base_endpoint.endswith("/v1/chat/completions"):
            return self.base_endpoint
        if self.api_type == "chat":
            return f"{self.base_endpoint}/v1/chat/completions"
        return f"{self.base_endpoint}/v1/completions"

    def complete(self, prompt: str, max_tokens: int = 800, temperature: float = 0.2) -> str:
        """调用LLM API完成文本生成"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = self._url()
        if self.api_type == "chat":
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        else:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices:
                first = choices[0]
                if self.api_type == "chat":
                    if isinstance(first, dict) and "message" in first and isinstance(first["message"], dict):
                        return first["message"].get("content", "")
                else:
                    if isinstance(first, dict) and "text" in first:
                        return first["text"]

        # Fallback to raw text response.
        if isinstance(data, str):
            return data
        return json.dumps(data, ensure_ascii=False)


