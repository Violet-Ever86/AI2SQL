import json
from typing import Dict, List

from model.llm_client import LLMClient


class Summarizer:
    """总结器类，负责对查询结果进行总结"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def summarize(self, question: str, sql: str, rows: List[Dict]) -> str:
        """总结查询结果"""
        total_rows = len(rows)
        preview = rows[:30] if total_rows > 0 else []

        if total_rows == 0:
            prompt = f"""你是数据总结助手。
                    用户问题：{question}
                    执行的SQL：{sql}
                    查询结果：空（0行数据）
                    请用中文回答：根据查询结果，没有找到相关数据。您可以提供更具体一些的问题吗？"""
        else:
            prompt = f"""你是数据总结助手。你总结是给老板看的。
                    用户问题：{question}
                    执行的SQL：{sql}
                    查询结果：共找到 {total_rows} 行数据（显示前{min(30, total_rows)}行）
                    数据内容（JSON格式）：
                    {json.dumps(preview, ensure_ascii=False, indent=2)}
                    特别强调：先写总结内容，然后关键信息，最后是记录概览 
                    
                    请根据上述查询结果，用中文简要回答用户问题。注意：
                    - 如果查询结果不为空，请基于实际数据内容回答
                    - 说明数据的时间范围、关键信息
                    - 如果数据较多，说明只显示了部分结果
                    - 先写总结内容，然后关键信息，最后是记录概览  """

        return self.llm_client.complete(prompt, max_tokens=10000, temperature=0.2)


