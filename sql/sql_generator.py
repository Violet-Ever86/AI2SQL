import json
import re
from typing import Dict, Tuple

from config.param_normalizer import ParamNormalizer
from sql.sql_templates import SQLTemplateManager


class SQLGenerator:
    """SQL生成器类，负责从自然语言生成SQL"""

    def __init__(self, param_normalizer: ParamNormalizer = None):
        self.param_normalizer = param_normalizer or ParamNormalizer()
        self.template_manager = SQLTemplateManager()

    def build_sql_prompt(self, question: str, schema_text: str) -> str:
        """构建SQL生成提示词"""
        # 构建模板列表描述
        templates_desc = self.template_manager.get_template_descriptions()

        system_rules = """
你是 SQL 生成助手。策略：
- 先尝试匹配“复杂/易错”模板，再填充参数。
- 如果觉得问题未命中模板，可直接自由生成单条 SELECT。
- 任何情况下都必须遵守：只用给定 schema 中的表/字段；只写一条 SELECT；禁止分号和多语句；必须包含 LIMIT；“最近/最新”需按时间倒序。

步骤：
1. 优先从下方“复杂/易错模板”选择最匹配的模板ID并提取参数
2. 若模板不合适，可直接自由生成 SQL
3. 输出严格 JSON，可两种格式：
   - 模板：{{"template_id": "T1", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.92}}
   - 自由生成：{{"template_id": "free", "sql": "SELECT ... LIMIT 20", "score": 0.0}}

可用模板列表：
""" + templates_desc + """

参数说明：
- person_name: 人员姓名（如"王飞"、"谢雁成"）
- archive_no: 档案编号（字符串）
- start_date/end_date: 日期范围（格式：YYYY-MM-DD）。如果只提供start_date，end_date默认为start_date（单日查询）
- target_date: 单个日期（格式：YYYY-MM-DD），用于查询某人在某日的记录
- limit: 返回条数（默认20，最大50）

模板选择提示：
- 如果问题包含人员姓名但未提及日期，在T1、T2、T26中选择最匹配的模板
- 如果问题包含人员姓名且提及日期，在T9、T10、T15、T16中选择最匹配的模板
- 如果问题未提及人员姓名只说最近的记录，在T4、T5、T6中选择最匹配的模板
- 如果问题包含编号，优先选择T7、T21、T27
- 有姓名且明确"跟班"字样（未提日期范围）：优先 T2；不要用 T5
- 有姓名且明确"带班"字样（未提日期范围）：优先 T1；不要用 T4
- 有姓名且出现"作业记录"或"工作记录"：优先 T26；不要用T6
- 意图映射提示（优先匹配再生成）：
  * “做了什么 / 干了什么 / 最近做了啥” → 理解为“工作记录（带班+跟班合并）”，按时间倒序，LIMIT 默认20，可用T26/T27思路
  * “带班了什么 / 带班记录” → 带班表，按时间倒序，LIMIT
  * “跟班了什么 / 跟班记录” → 跟班表，按时间倒序，LIMIT
  * 若上述典型都无法匹配，再自行生成单条 SELECT（只用给定表/字段，必须包含 LIMIT，禁止多语句/分号）

 输出格式（严格JSON）：
 {{"template_id": "模板ID", "params": {{"参数名": "参数值"}}, "score": 匹配度0到1之间的小数}}
 或
 {{"template_id": "free", "sql": "SELECT ... LIMIT 20", "score": 0.0}}
"""
        # 使用双花括号转义JSON中的花括号，避免f-string解析错误
        examples = """
示例：

问：王飞最近带班了哪些工序？
{{"template_id": "T1", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.95}}

问：王飞最近跟班了哪些工序？
{{"template_id": "T2", "params": {{"person_name": "王飞", "limit": 20}}}}

问：王飞最近做了什么（带班和跟班都要）？
{{"template_id": "T26", "params": {{"person_name": "王飞", "limit": 10}}, "score": 0.93}}

问：王飞最近干了啥？
{{"template_id": "T26", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.90}}

问：最近的记录就简单查一下（模型可自由生成）
{{"template_id": "free", "sql": "SELECT ... LIMIT 20", "score": 0.0}}

问：最近5条带班记录？
{{"template_id": "T4", "params": {{"limit": 5}}}}

问：最近5条跟班记录？
{{"template_id": "T5", "params": {{"limit": 5}}}}

问：最近5条工作记录？
{{"template_id": "T6", "params": {{"limit": 5}}}}

问：编号5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2的带班记录？
{{"template_id": "T21", "params": {{"archive_no": "5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2", "limit": 20}}}}

问：编号5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2的跟班记录？
{{"template_id": "T7", "params": {{"archive_no": "5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2", "limit": 20}}}}

问：编号5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2的最近20条工作记录？
{{"template_id": "T27", "params": {{"archive_no": "5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2", "limit": 20}}}}

问：2025年11月到12月的带班记录？
{{"template_id": "T8", "params": {{"start_date": "2025-11-01", "end_date": "2025-12-31", "limit": 20}}}}

问：谢雁成2025年11月14日的带班记录？
{{"template_id": "T9", "params": {{"person_name": "谢雁成", "target_date": "2025-11-14", "limit": 20}}}}

问：谢雁成2025年11月到12月的带班记录？
{{"template_id": "T10", "params": {{"person_name": "谢雁成", "start_date": "2025-11-01", "end_date": "2025-11-30", "limit": 20}}}}

问：谢雁成2025年11月14日的跟班记录？
{{"template_id": "T15", "params": {{"person_name": "谢雁成", "target_date": "2025-11-14", "limit": 20}}}}

问：谢雁成2025年11月到12月的跟班记录？
{{"template_id": "T16", "params": {{"person_name": "谢雁成", "start_date": "2025-11-01", "end_date": "2025-11-30", "limit": 20}}}}
"""

        prompt = f"""{system_rules}

可用的表结构：
{schema_text}
{examples}

现在请回答：
问：{question}
输出（仅JSON，不要其他文字）：
"""
        return prompt

    def extract_template_and_params(self, llm_output: str) -> Tuple[str, Dict, str, float]:
        """从模型输出中提取模板ID、参数、可选的自由SQL及匹配度，优先使用JSON解析方法"""
        print(f"llm_output:{llm_output}")

        # 清理输入文本
        json_str = llm_output.strip()
        # 去掉可能的代码块标记
        json_str = re.sub(r"^```(?:json)?", "", json_str, flags=re.I).strip()
        json_str = re.sub(r"```$", "", json_str).strip()
        # 处理转义的双花括号
        json_str = json_str.replace("{{", "{").replace("}}", "}")

        # 保存原始清理后的字符串，用于备用方法
        original_json_str = json_str

        # 方法1: 尝试直接解析整个字符串
        try:
            data = json.loads(json_str)
            return self._extract_from_dict(data)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"[DEBUG] 方法1失败: {e}")

        # 方法2: 提取第一个完整的JSON对象
        extracted_json = self._extract_json_object(json_str)
        if extracted_json:
            try:
                data = json.loads(extracted_json)
                return self._extract_from_dict(data)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"[DEBUG] 方法2失败: {e}")

        # 方法3: 尝试修复常见的JSON格式问题后解析（使用原始字符串）
        fixed_json = self._try_fix_json(original_json_str)
        if fixed_json and fixed_json != original_json_str:
            try:
                data = json.loads(fixed_json)
                return self._extract_from_dict(data)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"[DEBUG] 方法3失败: {e}")

        # 方法4: 如果所有JSON解析都失败，使用简单的正则表达式提取关键参数（作为最后手段）
        print(f"[DEBUG] 所有JSON解析方法都失败，使用正则表达式备用方法")
        return self._extract_with_regex_fallback(original_json_str, llm_output)

    def _extract_json_object(self, text: str) -> str:
        """从文本中提取第一个完整的JSON对象"""
        start_idx = text.find('{')
        if start_idx < 0:
            return ""

        brace_count = 0
        in_string = False
        escape_next = False

        for i in range(start_idx, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[start_idx:i + 1]

        return ""

    def _try_fix_json(self, json_str: str) -> str:
        """尝试修复常见的JSON格式问题"""
        # 移除注释（JSON不支持注释，但有些模型会输出）
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # 尝试修复单引号（JSON要求双引号）
        # 但要注意字符串内的单引号不应该被替换
        # 这里使用简单的方法：只替换键和值周围的单引号
        json_str = re.sub(r"'(\w+)'", r'"\1"', json_str)  # 键名
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # 字符串值

        return json_str

    def _extract_from_dict(self, data: Dict) -> Tuple[str, Dict, str, float]:
        """从解析好的字典中提取template_id、params、可选的自由SQL和匹配度score"""
        try:
            template_id = str(data.get("template_id", "")).strip()
            params_raw = data.get("params", {})
            sql_text = ""
            score = data.get("score", None)

            # 解析score，范围限制在[0,1]
            try:
                if score is not None:
                    score_val = float(score)
                    if score_val < 0:
                        score_val = 0.0
                    if score_val > 1:
                        score_val = 1.0
                else:
                    # 如果没给分数，模板默认1.0，自由模式默认0.0
                    if template_id and template_id.lower() != "free":
                        score_val = 1.0
                    else:
                        score_val = 0.0
            except (ValueError, TypeError):
                if template_id and template_id.lower() != "free":
                    score_val = 1.0
                else:
                    score_val = 0.0

            # 如果提供了自由生成的 SQL
            if "sql" in data and isinstance(data.get("sql"), str):
                sql_text = data.get("sql", "").strip()

            # 处理params可能是数组的情况
            if isinstance(params_raw, list):
                if len(params_raw) > 0 and isinstance(params_raw[0], dict):
                    params = params_raw[0].copy()
                else:
                    params = {}
            elif isinstance(params_raw, dict):
                params = params_raw.copy()
            else:
                params = {}

            # 确保params是字典
            if not isinstance(params, dict):
                params = {}

            # 规范化参数（保留所有原始参数）
            params = self.param_normalizer.normalize_params(params)

            # 如果模板选择了T9但没有target_date，则自动回退到T26
            if template_id == "T9":
                target_date = params.get("target_date", "")
                if not target_date:
                    template_id = "T26"
                    params.pop("target_date", None)

            return template_id, params, sql_text, score_val
        except Exception as e:
            print(f"[DEBUG] _extract_from_dict 异常: {type(e).__name__}: {e}")
            print(f"[DEBUG] data: {data}")
            raise

    def _extract_with_regex_fallback(self, json_str: str, original_output: str) -> Tuple[str, Dict, str, float]:
        """当JSON解析完全失败时的备用方法：使用正则表达式提取关键参数"""
        params = {"limit": 20}
        template_id = ""
        sql_text = ""

        # 如果json_str为空，使用original_output
        search_text = json_str if json_str else original_output

        # 提取template_id
        template_match = re.search(r'"template_id"\s*:\s*"([^"]+)"', search_text, re.I)
        if template_match:
            template_id = template_match.group(1).strip()

        # 提取所有可能的参数（使用简单的正则表达式）
        param_patterns = {
            "person_name": r'"person_name"\s*:\s*"([^"]+)"',
            "archive_no": r'"archive_no"\s*:\s*"([^"]+)"',
            "start_date": r'"start_date"\s*:\s*"([^"]+)"',
            "end_date": r'"end_date"\s*:\s*"([^"]+)"',
            "target_date": r'"target_date"\s*:\s*"([^"]+)"',
            "phone": r'"phone"\s*:\s*"([^"]+)"',
            "duty": r'"duty"\s*:\s*"([^"]+)"',
            "status": r'"status"\s*:\s*"([^"]+)"',
        }

        for key, pattern in param_patterns.items():
            match = re.search(pattern, search_text, re.I)
            if match:
                params[key] = match.group(1)

        # 提取limit（可能是数字）
        limit_match = re.search(r'"limit"\s*:\s*(\d+)', search_text, re.I)
        if limit_match:
            try:
                params["limit"] = int(limit_match.group(1))
            except ValueError:
                pass

        # 规范化参数
        params = self.param_normalizer.normalize_params(params)

        if not template_id:
            raise ValueError(f"无法从模型输出中解析模板ID和参数：{original_output[:200]}")

        # 正则兜底时，无法可靠给出score，这里给一个中等置信度
        score_val = 0.5

        return template_id, params, sql_text, score_val

    def generate_sql_from_template(self, template_id: str, params: Dict) -> str:
        """根据模板ID和参数生成SQL"""
        template = self.template_manager.get_template(template_id)

        # 规范化参数
        params = self.param_normalizer.normalize_params(params)

        sql = template["sql"]
        # 替换参数（使用format，但需要处理可能的缺失参数）
        try:
            # 为缺失的参数提供默认值
            default_params = {
                "person_name": "",
                "archive_no": "",
                "start_date": "1900-01-01",
                "end_date": "2099-12-31",
                "target_date": "",
                "department": "",
                "keyword": "",
                "phone": "",
                "duty": "",
                "status": "",
                "regular_flag": 1,
                "project_name": "",
                "limit": 20,
            }
            filled_params = {**default_params, **params}

            # 特殊处理：如果只提供了start_date而没有end_date，则end_date = start_date（单日查询）
            if "start_date" in params and "end_date" not in params:
                filled_params["end_date"] = filled_params["start_date"]

            sql = sql.format(**filled_params)
        except KeyError as e:
            raise ValueError(f"模板参数缺失: {e}")

        return sql

    def extract_sql(self, llm_output: str) -> str:
        """使用模板化方案：从模型输出提取模板ID和参数，生成SQL；支持自由SQL"""
        try:
            template_id, params, free_sql, _score = self.extract_template_and_params(llm_output)

            # 如果是自由生成且提供了sql字段，直接返回
            if template_id.lower() == "free" and free_sql:
                sql = free_sql
            else:
                sql = self.generate_sql_from_template(template_id, params)
            print(f"sql:{sql}")
            return sql
        except (ValueError, json.JSONDecodeError) as e:
            # 如果模板化失败，回退到原来的直接提取SQL方式
            print(f"警告：模板化解析失败，回退到直接提取SQL模式：{e}")
            m = re.search(r"SQL:\s*(.*)", llm_output, flags=re.S | re.I)
            if m:
                sql = m.group(1).strip()
            else:
                sql = llm_output.strip()
            # 去掉代码块符号
            sql = re.sub(r"^```[a-zA-Z0-9]*", "", sql).strip()
            sql = re.sub(r"```$", "", sql).strip()
            # 去掉末尾分号，避免误判多语句
            sql = sql.rstrip().rstrip(";").strip()
            print(f"sql:{sql}")
            return sql


