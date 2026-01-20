from config.config import params, logger
from llm_tools import tool_list
import requests


class LLMClient:
    # 使用config的通用模型配置实现交互功能
    def __init__(self, description, params=params):
        # 用以描述模型类别
        self.description = description

        # 模型基础配置
        self.llm_url = params.llm_url
        self.llm_model = params.llm_model
        self.llm_api_key = params.llm_api_key

        # 上下文
        self.context = []

        # 个性化工具
        self.allow_tools = []

    def response(self, query: str, tool_names: list[str]):
        # 根据上下文与工具构建请求体并生成回复
        self.remember("user", query)

        payload = {
            "model": self.llm_model,
            "messages": self.context,
            "tools": self.tool_add(tool_names),
        }

        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.llm_url, json=payload, headers=headers).json()
        self.remember("assistant", response)
        return response.json()

    def remember(self, role: str, content: str):
        self.context.append({role: content})

    def tool_add(self, tool_names: list[str]):
        tool_dict = tool_list

        tools = []
        for tool_name in tool_names:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_dict[tool_name]["description"],
                        "parameters": tool_dict[tool_name]["parameters"]
                    }
                }
            )
        return tools

if __name__ == '__main__':
    test_agent = LLMClient("测试", params=params)
    test_agent.response("你好")