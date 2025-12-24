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


参数说明（需要在 JSON 中给出的字段）：
- template_id: 模板ID，取值为 "M1" / "M2" / "M3" / "M4" / "free"
- person_name: 人员姓名（如"王飞"、"谢雁成"），当使用 M1/M2/M3/M4 时必须提供
- limit: 返回条数（默认20，SQL 内部会限制最大为 50）
- sql: 仅在 template_id="free" 时使用，表示你自由生成的完整 SQL 字符串
- score: 匹配度（0~1 的小数），表示你对所选模板或 SQL 的置信度；自由模式可以用 0.0

意图映射提示
- 以下为带班工作记录表/跟班工作记录表的 字段与扩展说明（帮助你理解表结构）：
    - 带班作业记录表/跟班工作记录表和记录带班/跟班的相关信息
    - 时间在带班作业记录表中对应为FGC_CreateDate(类型为2025-02-23 14:37:40.402761),在跟班作业记录表中对应为FGC_Rowversion(类型为2025-02-23 14:37:40.402761/最近默认为从当前时间倒数一个月
    - 地点在带班作业记录表中对应为带班作业工序及地点，在跟班作业记录表中对应为定位地址
    - 无指定人员就是查询所有人员，用档案编号查询就是用大桥局人员信息表的的档案编号。
    - 工作内容在带班作业记录表中对应为带班期间工作内容,跟班作业记录表中对应为重点部位_关键工序_特殊时段情况，,如果没有提及什么工作，那就是两个工作一起看。一起看时然后工作内容就是两个不同的内容。
    - 带班工程就是工程名称 跟班工程也是工程名称
    - 工程名称为类似的BM-00164编号
    - 其余就是表的字段对应查找
- 以下为大桥局人员信息表的 字段与扩展说明（帮助你理解表结构）：
    - 大桥局人员信息表记录每个人的相关信息
    - 档案编号为类似5eff5d2f-ad14-3336aed-9e93-f0ac281ab1e2的字符串
    -“单元长”可能出现在【职务】字段（正常情况），也可能异常出现在【岗位】字段。
        当 岗位 = '单元长' OR 职务 = '单元长' 时，判定为单元长。
    - 人数就是大桥局人员信息表的档案编号个数
    - 其余就是表的字段对应查找
- 以下为班前讲话班组字典表与责任单元字典表的 字段与扩展说明（帮助你理解表结构）：
    - 责任单元字典表.责任单元名称(如东山跨海特大桥420#-491#平台搭设及下构施工)是指班组负责的单元地方/部位，也就是该跟班的工作地点
    - 责任单元字典表.单元长姓名是指该单元负责人
    - 责任单元字典表.工程类型名称是指该单元的类型。责任单元字典表.工程类型名称不是责任单元字典表.工程类型。
    - 责任单元字典表.工程类型如路基工程,桥梁工程,隧道工程。 可能是多个工程类型混合
    - 责任单元字典表.状态是指该单元是施工还是停工
    - 责任单元字典.档案编号 与大桥局人员信息表.档案编号 对应，通过对应关系可以在大桥局人员信息表查询该单元负责人基本信息
    - 班前讲话班组字典.班组是指该班组的具体班组名称
    - 班前讲话班组字典.班组长是指班组长名称
    - 班前讲话班组字典.手机号是指班组长的手机号
    - 班前讲话班组字典.班组成员是指班组成员
    - 班前讲话班组字典.公司是指班组的公司
    -班前讲话班组字典.所属项目是指班组所属项目
    - 班前讲话班组字典表.安全责任单元 与 责任单元字典.ID 对应
    - 责任单元字典表是负责的地方，部位，以及该地方的负责人和状态。
    - 班前讲话班组字典表 就是用来查看班组对应的一些信息
    - 班前讲话班组字典表.班组ID 与 跟班作业记录表.班组 对应 ,不是班前讲话班组字典表.班组 与 跟班作业记录表.班组 对应 
- 以下为每日管控计划，每日管控计划_子表与安全责任单元履职清单主表的 字段与扩展说明（帮助你理解表结构）：
    -安全责任单元履职清单主表.ID 对应 每日管控计划_子表.工序id字符串  
    -安全责任单元履职清单主表.名称 就是对应的工序的名称，工序有顺序，安全责任单元履职清单主表.级别就是顺序
    -安全责任单元履职清单主表.上级ID 对应 安全责任单元履职清单主表.ID 就是指 当前工序的上一级工序
        举个例子 安全责任单元履职清单主表中ID为15 名称为路基开挖，表示工序为路基开挖，级别为2，说明第2级，上级ID为2，说明 安全责任单元履职清单主表中ID为2，名称为路基开挖为他的上一步工序
    -每日管控计划.管控单元id 与 责任单元字典.ID 对应 ，因此每日管控计划.管控单元id可以了解管控计划的单元地方/部位，该单元负责人等等
    -每日管控计划.管控责任人 就是管控计划负责人
    -每日管控计划.状态 只有两种状态 已提交和暂缓 ，就是指计划是否提交了
    -每日管控计划.计划日期就是计划时间
    -每日管控计划_子表 是每日管控计划的内容补充
    -每日管控计划_子表.每日管控计划_ID =每日管控计划.ID
    -每日管控计划_子表.工序id字符串 对应 安全责任单元履职清单主表.ID  每日管控计划_子表.工序id字符串格式为105,131,132,133，可能工序id字符串有多个工序id
    -每日管控计划_子表.管控人员 是指管控计划中的相关人员，风险研判，责任单元长，技术员，安全员，施工员机管员
    -每日管控计划_子表.风险研判 是指管控计划中风险
    -每日管控计划_子表.管控措施 是指管控计划中措施
    -每日管控计划_子表.领导带班 为bool类型，1就是有，空就是无。每日管控计划_子表.带班领导档案就是带班人员领导的领导档案编号
    -每日管控计划_子表.领导跟班 为bool类型，1就是有，空就是无。每日管控计划_子表.跟班人档案就是跟班人员领导的领导档案编号
    -带班作业记录表.工单子表ID 与 每日管控计划_子表.ID 对应，带班作业记录表.工单子表ID10 就说明 这个记录是每日管控计划子表ID10中的计划的带班记录
    -跟班作业记录表.工单子表ID 与 每日管控计划_子表.ID 对应，跟班作业记录表.工单子表ID10 就说明 这个记录是每日管控计划子表ID10中的计划的跟班记录
    -管控计划内容在每日管控计划_子表.分项名称和每日管控计划.施工计划作业内容中间
        例如管控计划内容为“2掌子面正常开挖进尺，仰拱钢筋绑扎，二衬铺设防水板”可能是每日管控计划_子表.分项名称和每日管控计划.施工计划作业内容的一部分
- “某人带班了什么 / 最近带了哪些班？” (一定是某人的名字 )→ 使用 M1：按姓名查询带班作业记录表，返回【带班日期、带班作业工序及地点】，按时间倒序，LIMIT<=50。
- “某人跟班了什么 / 最近跟了哪些班？” → 使用 M2：按姓名查询跟班作业记录表，返回【日期、重点部位_关键工序_特殊时段情况】，按时间倒序，LIMIT<=50。
  **注意**：这里的"某人"必须是人员姓名（如"王飞"、"罗康康"），不是班组名。
- “某人最近做了什么（带班+跟班都要）？ ” → 使用 M3：按姓名合并带班+跟班记录，统一返回【时间、类型、人员、作业内容、发生日期】，按时间倒序，LIMIT<=50。
  **注意**：这里的"某人"必须是人员姓名，不是班组名。
- “某人的详细信息（档案编号、岗位、职务、手机号、状态、所属部门、所属项目）？” → 使用 M4：按姓名查询大桥局人员信息表。
- "某班组的跟班记录 / 查询某班组的跟班作业 / 某公司班组的跟班记录" → 使用 M5：通过班前讲话班组字典.班组查询跟班作业记录表，返回【日期、重点部位_关键工序_特殊时段情况】，按时间倒序，LIMIT<=50。
  **注意**：这里的"某班组"必须是班组名称（如"武汉化工"、"第一班组"、"XX公司班组"），不是人员姓名。如果问题中包含"班组"、"公司"等关键词，或者名称看起来像组织/单位名称，应使用M5而不是M2。
- "查询管控计划内容的状态 / 某管控计划内容的状态是什么" → 使用 M6：通过管控计划内容查询每日管控计划的状态，内容可能在每日管控计划_子表.分项名称或每日管控计划.施工计划作业内容中，返回【状态、计划日期、施工计划作业内容、分项名称】，按时间倒序，LIMIT<=50。
  **重要区分**：
  - M6用于直接查询"管控计划内容"的状态，问题中应该明确提到"管控计划内容"或"管控计划"+"内容"
  - **不要**使用M6处理以下情况：
    * "跟班任务XXX的管控计划是几号" → 应该使用自由SQL，通过跟班作业记录表.重点部位_关键工序_特殊时段情况匹配，然后通过工单ID关联到每日管控计划
    * "带班任务XXX的管控计划" → 应该使用自由SQL，通过带班作业记录表.带班作业工序及地点匹配，然后通过工单ID关联到每日管控计划
  - M6只用于：已知管控计划内容（如"掌子面正常开挖进尺"），想查询这个内容对应的管控计划状态
- 
- **重要区分规则**：
  - 如果问题中提到的是人名（如"王飞"、"罗康康"、"张三"等常见人名格式），使用 M2（按姓名查询跟班记录）
  - 如果问题中提到的是班组名（如"武汉化工"、"第一班组"、"XX公司"、"XX班组"等），使用 M5（按班组名称查询跟班记录）
  - 如果问题中明确包含"班组"、"公司"等关键词，优先使用 M5
  - 如果问题中只提到名称且没有明确是"班组"或"公司"，根据名称特征判断：人名通常2-4个汉字，班组名可能更长或包含"公司"、"班组"等词
  - **M6使用场景**：问题明确提到"管控计划内容"或"管控计划"+"内容"，且不是通过跟班/带班任务来查找管控计划
  - **不要用M6的场景**：如果问题是"跟班任务XXX的管控计划"或"带班任务XXX的管控计划"，应该使用自由SQL模式，通过跟班作业记录表/带班作业记录表的工单ID关联到每日管控计划
- 如果问题超出以上典型场景，且你能根据 schema 自己写出安全的 SQL，可以使用 template_id="free" 并直接返回 sql。


 - 使用模板（M1~M6）：
  {{"template_id": "M1", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.95}}
  {{"template_id": "M2", "params": {{"person_name": "罗康康", "limit": 20}}, "score": 0.94}}
  {{"template_id": "M5", "params": {{"team_name": "武汉化工", "limit": 20}}, "score": 0.93}}
  {{"template_id": "M6", "params": {{"plan_content": "掌子面正常开挖进尺", "limit": 20}}, "score": 0.92}}
- 自由生成：
  {{"template_id": "free", "sql": "SELECT ... LIMIT 20", "score": 0.0}}
"""
        # 使用双花括号转义JSON中的花括号，避免f-string解析错误
        examples = """
示例：

问：王飞最近带班了哪些工序？
{{"template_id": "M1", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.95}}
说明：王飞是人名，使用M1

问：王飞最近跟班了哪些工序？
{{"template_id": "M2", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.94}}
说明：王飞是人名，使用M2

问：查询武汉化工的跟班记录？
{{"template_id": "M5", "params": {{"team_name": "武汉化工", "limit": 20}}, "score": 0.93}}
说明：武汉化工是班组/公司名称，使用M5

问：罗康康的跟班记录？
{{"template_id": "M2", "params": {{"person_name": "罗康康", "limit": 20}}, "score": 0.94}}
说明：罗康康是人名，使用M2

问：第一班组的跟班作业？
{{"template_id": "M5", "params": {{"team_name": "第一班组", "limit": 20}}, "score": 0.93}}
说明：第一班组是班组名称，使用M5

问：王飞最近做了什么（带班和跟班都要）？
{{"template_id": "M3", "params": {{"person_name": "王飞", "limit": 20}}, "score": 0.93}}
说明：王飞是人名，使用M3

问：谢雁成的详细信息？
{{"template_id": "M4", "params": {{"person_name": "谢雁成"}}, "score": 0.9}}
说明：谢雁成是人名，使用M4

问：查询管控计划内容"掌子面正常开挖进尺"的状态？
{{"template_id": "M6", "params": {{"plan_content": "掌子面正常开挖进尺", "limit": 20}}, "score": 0.92}}
说明：查询管控计划内容的状态，使用M6

问：跟班任务"掌子面初期支护，仰拱衬砌"的管控计划是几号？
{{"template_id": "free", "sql": "SELECT p.计划日期, p.ID, g.重点部位_关键工序_特殊时段情况 FROM 跟班作业记录表 AS g JOIN 每日管控计划 AS p ON g.工单ID = p.ID WHERE g.重点部位_关键工序_特殊时段情况 LIKE '%掌子面初期支护%' OR g.重点部位_关键工序_特殊时段情况 LIKE '%仰拱衬砌%' ORDER BY COALESCE(p.FGC_CreateDate, p.计划日期, p.FGC_LastModifyDate) DESC LIMIT 20", "score": 0.0}}
说明：通过跟班任务查找管控计划，不是查询管控计划内容的状态，应该使用自由SQL，通过跟班作业记录表关联到每日管控计划

问：简单查一下最近的记录（你可以自由生成 SQL）
{{"template_id": "free", "sql": "SELECT ... LIMIT 20", "score": 0.0}}
"""
        prompt = f"""{system_rules}

可用的表结构：
{schema_text}
{examples}

现在请回答：
问：{question}
输出（仅JSON，不要其他文字）：
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
            "team_name": r'"team_name"\s*:\s*"([^"]+)"',
            "plan_content": r'"plan_content"\s*:\s*"([^"]+)"',
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
                "team_name": "",
                "plan_content": "",
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


