import json
import time
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

    def complete(self, prompt: str, max_tokens: int = 10000, temperature: float = 0.2) -> str:
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

        # 为LLM请求增加简单的重试机制，缓解偶发的连接被远程中断问题
        max_retries = 3
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.RequestException as e:
                last_exception = e
                # 连接被远程主机重置等网络类错误，稍等后重试
                print(f"\n警告：第 {attempt} 次调用 LLM 接口失败：{e}")
                if attempt == max_retries:
                    # 重试多次仍失败，向上抛出，让上层捕获并展示错误
                    raise
                time.sleep(1.0)

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


