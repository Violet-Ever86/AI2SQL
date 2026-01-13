import json
from typing import Dict, List

from model.llm_client import LLMClient
from config.config import logger


class Summarizer:
    """总结器类，负责对查询结果进行总结"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def summarize(self, question: str, sql: str, rows: List[Dict]) -> Dict:
        """总结查询结果，返回结构化数据"""
        total_rows = len(rows)
        preview = rows[:30] if total_rows > 0 else []

        if total_rows == 0:
            prompt = f"""你是数据总结助手。
                    用户问题：{question}
                    执行的SQL：{sql}
                    查询结果：空（0行数据）
                    
                    请以JSON格式返回结果，格式如下：
                    {{
                        "summaryContent": "根据查询结果，没有找到相关数据。您可以提供更具体一些的问题吗？",
                        "keyInfo": "",
                        "recordOverview": ""
                    }}
                    
                    请确保返回的是有效的JSON格式，不要包含其他文字说明。"""
        else:
            prompt = f"""你是数据总结助手。你总结是给老板看的，所以不要出现那种技术文字，如"a"=1 这sql语句。
                    用户问题：{question}
                    执行的SQL：{sql}
                    查询结果：共找到 {total_rows} 行数据（显示前{min(30, total_rows)}行）
                    数据内容（JSON格式）：
                    {json.dumps(preview, ensure_ascii=False, indent=2)}
                    
                    【图表工具说明】
                    你可以在总结中使用图表来可视化数据，让数据更直观易懂。支持的图表类型：
                    1. bar - 柱状图（适合比较不同类别的数值，如月度销售额对比）
                    2. line - 折线图（适合显示趋势变化，如时间序列数据）
                    3. pie - 饼图（适合显示占比关系，如各类别占比）
                    4. area - 面积图（适合显示累积趋势，如累计增长）
                    
                    图表指令格式（在文本中嵌入JSON对象）：
                    {{"chart": {{
                        "type": "bar|line|pie|area",
                        "title": "图表标题",
                        "data": [
                            {{"label": "类别1", "value": 数值1}},
                            {{"label": "类别2", "value": 数值2}}
                        ],
                        "xLabel": "X轴标签（可选，仅用于bar/line/area）",
                        "yLabel": "Y轴标签（可选，仅用于bar/line/area）"
                    }}}}
                    
                    使用建议：
                    - 如果数据适合可视化（如有多组对比数据、时间序列、占比关系），可以在summaryContent或keyInfo中插入图表指令
                    - 图表指令必须是有效的JSON对象，可以直接嵌入在文本中
                    - 确保data数组中的value是数字类型
                    - 图表应该与文本内容相关，帮助说明数据特点
                    
                    请根据上述查询结果，以JSON格式返回总结，格式如下：
                    {{
                        "summaryContent": "总结内容：简要回答用户问题，说明查询结果的核心信息",
                        "keyInfo": "关键信息：说明数据的时间范围、关键数值、重要发现等",
                        "recordOverview": "记录概览：说明数据的总数、数据范围、是否显示完整等",
                        "charts": [
                            {{
                                "type": "bar",
                                "title": "图表标题",
                                "data": [
                                    {{"label": "类别1", "value": 数值1}},
                                    {{"label": "类别2", "value": 数值2}}
                                ],
                                "xLabel": "X轴标签（可选，仅用于bar/line/area）",
                                "yLabel": "Y轴标签（可选，仅用于bar/line/area）"
                            }}
                        ]
                    }}
                    
                    要求：
                    - 必须返回有效的JSON格式，不要包含其他文字说明
                    - summaryContent：简要回答用户问题，说明查询结果的核心信息
                    - keyInfo：说明数据的时间范围、关键数值、重要发现等关键信息
                    - recordOverview：说明数据的总数、数据范围、是否显示完整等概览信息
                    - charts：图表数组（可选），如果数据适合可视化，可以添加图表配置
                      - 每个图表对象包含：type（图表类型）、title（图表标题）、data（数据数组）
                      - data数组中每个元素包含：label（标签）和value（数值）
                      - 如果不需要图表，charts可以设置为空数组[]
                    - 如果某个字段没有内容，可以设置为空字符串
                    - 所有内容都用中文回答"""

        response = self.llm_client.complete(prompt, max_tokens=10000, temperature=0.2)
        logger.debug("[LLM总结] LLM调用完成")
        # 尝试解析JSON响应
        try:
            # 移除可能的markdown代码块标记
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            # 解析JSON
            summary_dict = json.loads(response)

            # 验证必需字段
            if not isinstance(summary_dict, dict):
                raise ValueError("响应不是字典格式")

            # 确保所有字段都存在
            result = {
                "summaryContent": summary_dict.get("summaryContent", ""),
                "keyInfo": summary_dict.get("keyInfo", ""),
                "recordOverview": summary_dict.get("recordOverview", ""),
                "charts": summary_dict.get("charts", [])  # 图表数组
            }
            logger.debug("[LLM总结] 总结生成完成")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            # 如果解析失败，返回默认结构，将原始响应作为总结内容
            logger.warning("[LLM总结] 总结生成完成（JSON解析失败，使用原始响应）")
            return {
                "summaryContent": response,
                "keyInfo": "",
                "recordOverview": ""
            }


