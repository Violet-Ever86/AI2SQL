import requests
import argparse

parser = argparse.ArgumentParser(description="生产环境参数配置")
# 大模型配置
parser.add_argument('--llm_url', default='https://ai-api.crec.cn/v1', help='LLM API端点')
# parser.add_argument('--llm_url', default='http://10.84.9.9:65530/v1/chat-messages', help='LLM API端点')
parser.add_argument('--llm_model',   default='DeepSeek-V3.1:671B', help='LLM模型名称')
# parser.add_argument('--llm_api_key', default='app-fBXKA9AHjcRjW9rxi7EeJUSn', help='LLM API密钥')
parser.add_argument('--llm_api_key', default='sk-ypyAh4NQw0DT95UGcHlRlHyDV76zKEmg8wZuXkNQpwV4V4LF', help='LLM API密钥')
parser.add_argument('--llm_api_type',default='chat', choices=['completion','chat'], help='LLM API类型')

params = parser.parse_args()

class LLMClient:
    # 使用config的通用模型配置实现交互功能
    def __init__(self, description, params=params):
        # 用以描述模型类别
        self.description = description
        # 模型基础配置
        self.llm_url = params.llm_url
        self.llm_model = params.llm_model
        self.llm_api_key = params.llm_api_key


    def response(self, query):

        payload = {
            "model": self.llm_model,
            "messages": {"user": query},
        }

        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.llm_url, json=payload, headers=headers).json()
        return response.json()


if __name__ == '__main__':
    test_agent = LLMClient("测试", params=params)
    test_agent.response("你好")