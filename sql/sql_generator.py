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

        system_rules = ("""
        你是一位专业且高效的数据库工程师，精通SQL生成、数据总结分析与图表绘制；
        你解决问题的方式总是遵循“分析问题——生成SQL——根据查询结果进行总结与图表绘制”的流程。
        你需要根据实际的问题严格调用对应功能的工具，并且**绝对**禁止**在 content 中回复**任何**内容，所有的回复都**必须**只能**通过调用工具实现。
        其中，SQL的生成步骤如下：
        1、先尝试匹配已有的用以“高频查询、复杂查询”的模板：
        2-1、如果问题与某个模板相似，且问题的信息含量少于等于模板，则必须完全使用该模板。
        2-2、如果问题不匹配任何已有模板，或者问题的信息含量大于模板，就必须自由生成sql语句。
        3-1、如果匹配到了相似模板，就需要*提取参数*；如果是在模板的基础上增加或是自由生成sql，则不需要。
        4、最后的输出必须严格调用工具函数。根据sql的生成策略，分为两个工具：
        - 当通过匹配模板得到SQL语句时，调用 select_templates 函数；
        - 当通过自由生成模式得到SQL语句时，调用 generate_sql 函数。
        
        **sql生成要求**重要**任何情况下都必须遵守：**
        1、必须且只能使用给定 schema 中的表/字段；
        2、必须且只能写一条 SELECT；
        3、禁止分号和多语句；
        4、自由生成SQL时，说明用户的输入包含了隐藏的查询意图。你必须根据schema揣测意图，并依此选择更多相关字段以输出尽可能多的信息。必须优先选择业务相关的字段（如姓名、日期、地点、工作内容、状态等），禁止选择[FGC、电子签名]等无意义的字段。
        5、优先使用INNER JOIN而非LEFT JOIN；如果必须使用LEFT JOIN，需要在WHERE子句中过滤掉NULL值（如 `关联表.关键字段 IS NOT NULL`）。
        可用模板列表：
        """ +
        templates_desc
        + """
        现有表格的整体介绍：
        1. 安全责任单元履职清单主表、大桥局人员信息表、带班作业记录表、跟班作业记录表、每日管控计划、每日管控计划_子表、责任单元字典 为一个模块，命名为模块一。
            1.1 本模块主要以工作内容和计划内容为查询视角，其它视角需根据已有规则自行推理。
            1.2 带班作业记录表、跟班作业记录表、每日管控计划、每日管控计划_子表为主体表，凡涉及工作内容或计划内容均优先从这几张表查询。
            1.3 带班作业记录表表示带班任务，跟班作业记录表表示跟班任务。
            1.4 每日管控计划为主表，每日管控计划_子表为明细表，一个主表可对应多个子表。
            1.5 涉及人员信息（除班组人员），从相关业务表关联到大桥局人员信息表。
            1.6 涉及工程逻辑顺序或工作类型，从每日管控计划_子表关联到安全责任单元履职清单主表。
            1.7 涉及班组信息，从跟班作业记录表关联到班前讲话班组字典。
            1.8 涉及单元负责人员信息，从班前讲话班组字典或每日管控计划关联到责任单元字典。
            1.9 一个项目包含多个网格，网格即责任单元，每个网格对应班组完成内容。
        意图映射提示    
        1、模块一的意图映射
            1.1 查询管控计划内容：每日管控计划.施工计划作业内容
            1.2、查询跟班任务内容：跟班作业记录表.重点部位_关键工序_特殊时段情况
            1.3、查询带班任务内容：带班作业记录表.带班期间工作内容
            1.4、查询管控计划地点：每日管控计划_子表.分项名称
            1.5、工作内容包含跟班任务内容与带班任务内容，工作计划指管控计划内容。
            1.6、查询管控计划内容下面的工作是否存在：
                1.查询管控计划内容对应的每日管控计划_子表
                2.通过每日管控计划_子表查询每日管控计划_子表.领导带班和每日管控计划_子表.跟导跟班
                3.如果存在跟班领导，通过跟班作业记录表.工单子表ID=每日管控计划_子表.ID，查询跟班任务内容
                4.如果存在带班领导，通过带班作业记录表.工单子表ID=每日管控计划_子表.ID，查询带班任务内容
            1.7、查询工作状态/计划状态:查询跟班作业记录表.状态或者带班作业记录表.状态或者每日管控计划.状态
            1.8、查询管控计划所属网格：通过每日管控计划.管控单元id =责任单元字典.ID 查询责任单元字典.责任单元名称
            1.9、查询跟班任务的班组中文名称:通过跟班作业记录表.ID=班前讲话班组字典.班组名称，查询班前讲话班组字典.班组。
                （依次类推查询班组长的其余信息(除开班组负责人）的都在班前讲话班组字典）
            1.10、查询跟班任务所属网格:
                1.通过跟班作业记录表.ID=班前讲话班组字典.班组名称，查询班前讲话班组字典安全责任单元 
                2.通过班前讲话班组字典安全责任单元=责任单元字典.ID 查询责任单元字典.工程类型名称
                 （依次类推查询班组负责人的信息以及单元工程类型的都在责任单元字典）
            1.11、查询某工程的上级，下级。
                1.通过安全责任单元履职清单主表查询，查询安全责任单元履职清单主表.名称，安全责任单元履职清单主表.级别，安全责任单元履职清单主表.ID
                2.首先通过安全责任单元履职清单主表.ID=全责任单元履职清单主表.级别，查询对应的下级工程名称即安全责任单元履职清单主表.名称
                3.然后通过全责任单元履职清单主表.级别=安全责任单元履职清单主表.ID，查询对应的上一级工程名称即安全责任单元履职清单主表.名称（多次重复找到最上级）
                举个例子 安全责任单元履职清单主表中ID为15 名称为路基开挖，表示工序为路基开挖，级别为2，说明第2级，上级ID为2，说明 安全责任单元履职清单主表中ID为2，名称为路基开挖为他的上一步工序
        **自由生成SQL的重要要求**：
        - 请仔细阅读schema_prompt.txt中每个字段的说明，理解字段的含义和用途
         - 在SELECT子句中尽可能选择更多相关字段，输出尽可能多的信息
        - 优先选择业务相关的字段（如姓名、日期、地点、工作内容、状态、备注等），避免只选择ID等无意义的字段
        - 如果涉及关联查询，请通过JOIN获取关联表的更多信息（如人员姓名、单元名称等）
        - 确保SQL能够提供足够的信息来回答用户的问题
        """)

        examples = """
示例：

问：罗康康的跟班记录？
select_templates(id="M2", params={"person_name": "罗康康"})

问：班组武汉化工的跟班作业？
select_templates(id="M5", params={"team_name": "武汉化工"})

问：王飞最近做了什么？
select_templates(id="M3", params={"person_name": "王飞"})
# # # 

问：谢雁成的详细信息？
{{"template_id": "M4", "params": {{"person_name": "谢雁成"}}}}
说明：谢雁成是人名，使用M4

问：2025年3月5号路基L21的管控计划详情？
{{"template_id": "M6", "params": {{"date": "2025-03-05", "unit_name": "路基L21"}}}}
说明：问题包含日期（2025年3月5号）和单元名称（路基L21），使用M6，必须同时提供date和unit_name参数

问：跟班任务"掌子面初期支护，仰拱衬砌"的管控计划是几号？
{{"template_id": "free", "sql": "SELECT p.计划日期, p.ID, p.管控责任人档案编号, p.状态, p.施工计划作业内容, g.重点部位_关键工序_特殊时段情况, g.日期, g.跟班人员, g.定位地址 FROM 跟班作业记录表 AS g JOIN 每日管控计划 AS p ON g.工单ID = p.ID WHERE g.重点部位_关键工序_特殊时段情况 LIKE '%掌子面初期支护%' OR g.重点部位_关键工序_特殊时段情况 LIKE '%仰拱衬砌%' ORDER BY COALESCE(p.FGC_CreateDate, p.计划日期, p.FGC_LastModifyDate) DESC"}}
说明：通过跟班任务查找管控计划，不是查询管控计划内容的状态，应该使用自由SQL，通过跟班作业记录表关联到每日管控计划。注意：这里选择了多个相关字段以提供更多信息

问：简单查一下最近的记录（你可以自由生成 SQL）
{{"template_id": "free", "sql": "SELECT g.日期, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.定位地址, g.安全质量__管控情况__, g.状态, p.姓名 AS 跟班人员姓名 FROM 跟班作业记录表 AS g INNER JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号 ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC"}}
说明：自由生成SQL时，选择了多个相关字段（日期、工作内容、人员、地点、状态等），并通过INNER JOIN获取了人员姓名，提供了尽可能多的信息。注意：这里使用INNER JOIN而不是LEFT JOIN，因为我们需要确保关联到有效的人员信息

问：查询所有跟班记录，包括没有人员信息的记录（示例：必须使用LEFT JOIN的情况）
{{"template_id": "free", "sql": "SELECT g.日期, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.定位地址, p.姓名 AS 跟班人员姓名 FROM 跟班作业记录表 AS g LEFT JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号 WHERE p.档案编号 IS NOT NULL ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC"}}
说明：如果问题明确要求包含所有记录（即使没有关联信息），可以使用LEFT JOIN，但必须在WHERE子句中添加 `p.档案编号 IS NOT NULL` 来过滤掉NULL值，避免返回无意义的记录
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

    def extract_template_and_params(self, llm_output: str) -> Tuple[str, Dict, str]:
        """从模型输出中提取模板ID、参数、可选的自由SQL，优先使用JSON解析方法"""
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

        # 检查输出是否明显不完整
        if original_json_str.startswith('{') and not original_json_str.rstrip().endswith('}'):
            raise ValueError(f"模型输出不完整（JSON未闭合）。输出内容: {original_json_str[:200]}...")

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

    def _extract_from_dict(self, data: Dict) -> Tuple[str, Dict, str]:
        """从解析好的字典中提取template_id、params、可选的自由SQL"""
        try:
            template_id = str(data.get("template_id", "")).strip()
            params_raw = data.get("params", {})
            sql_text = ""

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

            return template_id, params, sql_text
        except Exception as e:
            print(f"[DEBUG] _extract_from_dict 异常: {type(e).__name__}: {e}")
            print(f"[DEBUG] data: {data}")
            raise

    def _extract_with_regex_fallback(self, json_str: str, original_output: str) -> Tuple[str, Dict, str]:
        """当JSON解析完全失败时的备用方法：使用正则表达式提取关键参数"""
        params = {}
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
            "team_name": r'"team_name"\s*:\s*"([^"]+)"',
            "unit_name": r'"unit_name"\s*:\s*"([^"]+)"',
            "archive_no": r'"archive_no"\s*:\s*"([^"]+)"',
            "date": r'"date"\s*:\s*"([^"]+)"',
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

        # 规范化参数
        params = self.param_normalizer.normalize_params(params)

        if not template_id:
            raise ValueError(f"无法从模型输出中解析模板ID和参数：{original_output[:200]}")

        return template_id, params, sql_text

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
                "team_name": "",
                "unit_name": "",
                "archive_no": "",
                "date": "",
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
            template_id, params, free_sql = self.extract_template_and_params(llm_output)

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


