"""SQL模板定义和管理模块"""

# SQL 模板定义：每个模板包含ID、描述、SQL模板（用 {参数} 占位）
SQL_TEMPLATES = [
    {
        "id": "T1",
        "desc": "查询指定人员最近的带班记录（通过姓名）",
        "sql": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}'
ORDER BY COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) DESC
LIMIT {limit}"""
    },
    {
        "id": "T2",
        "desc": "查询指定人员最近的跟班记录（通过姓名，需关联人员表）",
        "sql": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}'
ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC
LIMIT {limit}"""
    },
    {
        "id": "T4",
        "desc": "查询最近N条带班记录（不限人员）",
        "sql": """SELECT 带班人员, 带班作业工序及地点, 带班日期, 带班开始时间, 带班结束时间
FROM 带班作业记录表
ORDER BY COALESCE(FGC_CreateDate, 带班日期, FGC_LastModifyDate) DESC
LIMIT {limit}"""
    },
    {
        "id": "T5",
        "desc": "查询最近N条跟班记录（不限人员）",
        "sql": """SELECT 跟班人员, 重点部位_关键工序_特殊时段情况, 日期, 班组
FROM 跟班作业记录表
ORDER BY COALESCE(FGC_CreateDate, 日期, FGC_LastModifyDate) DESC
LIMIT {limit}"""
    },
    {
        "id": "T6",
        "desc": "查询最近N条工作记录（带班+跟班合并，不限人员）",
        "sql": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
FROM (
  SELECT COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) AS ts,
         '带班' AS 类型,
         b.带班人员档案编号 AS 人员,
         b.带班作业工序及地点 AS 作业内容,
         b.带班日期 AS 发生日期
  FROM 带班作业记录表 AS b
  UNION ALL
  SELECT COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) AS ts,
         '跟班' AS 类型,
         g.跟班人员 AS 人员,
         g.重点部位_关键工序_特殊时段情况 AS 作业内容,
         g.日期 AS 发生日期
  FROM 跟班作业记录表 AS g
) AS t
ORDER BY ts DESC
LIMIT {limit}"""
    },
    {
        "id": "T7",
        "desc": "按档案编号查询人员最近的跟班记录",
        "sql": """SELECT 日期, 班组, 重点部位_关键工序_特殊时段情况, 跟班人员, 跟班人员档案编号
FROM 跟班作业记录表
WHERE 跟班人员档案编号 = '{archive_no}'
ORDER BY COALESCE(FGC_CreateDate, 日期, FGC_LastModifyDate) DESC
LIMIT {limit}"""
    },
    {
        "id": "T8",
        "desc": "查询指定日期范围的带班记录（不限人员）",
        "sql": """SELECT 带班人员, 带班作业工序及地点, 带班日期, 带班开始时间, 带班结束时间
FROM 带班作业记录表
WHERE 带班日期 >= '{start_date}' AND 带班日期 <= '{end_date}'
ORDER BY 带班日期 DESC
LIMIT {limit}"""
    },
    {
        "id": "T9",
        "desc": "查询指定人员在指定日期的带班记录（人员+日期）",
        "sql": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND b.带班日期 = '{target_date}'
ORDER BY b.带班开始时间
LIMIT {limit}"""
    },
    {
        "id": "T10",
        "desc": "查询指定人员在指定日期范围的带班记录（人员+日期范围）",
        "sql": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND b.带班日期 >= '{start_date}' AND b.带班日期 <= '{end_date}'
ORDER BY b.带班日期 DESC
LIMIT {limit}"""
    },
    {
        "id": "T11",
        "desc": "查询人员信息表中某人的详细信息（通过姓名）",
        "sql": """SELECT 档案编号, 姓名, 岗位, 职务, 手机号, 状态, 所属部门, 所属项目
FROM 大桥局人员信息表
WHERE 姓名 = '{person_name}'
LIMIT 1"""
    },
    {
        "id": "T12",
        "desc": "统计人员信息表的总人数",
        "sql": """SELECT COUNT(*) AS 人员总数
FROM 大桥局人员信息表"""
    },
    {
        "id": "T13",
        "desc": "按状态统计人员数量（例如在职/离职/停职等）",
        "sql": """SELECT 状态, COUNT(*) AS 人数
FROM 大桥局人员信息表
WHERE 状态 = '{status}'
GROUP BY 状态"""
    },
    {
        "id": "T15",
        "desc": "查询指定人员在指定日期的跟班记录（人员+日期）",
        "sql": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND g.日期 = '{target_date}'
ORDER BY g.日期
LIMIT {limit}"""
    },
    {
        "id": "T16",
        "desc": "查询指定人员在指定日期范围的跟班记录（人员+日期范围）",
        "sql": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND g.日期 >= '{start_date}' AND g.日期 <= '{end_date}'
ORDER BY g.日期 DESC
LIMIT {limit}"""
    },
    {
        "id": "T20",
        "desc": "按手机号查询人员详细信息",
        "sql": """SELECT 档案编号, 姓名, 岗位, 职务, 手机号, 状态, 所属部门, 所属项目
FROM 大桥局人员信息表
WHERE 手机号 = '{phone}'
LIMIT 1"""
    },
    {
        "id": "T21",
        "desc": "按档案编号查询最近的带班记录（含联系方式）",
        "sql": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间,
       p.姓名, p.手机号, p.岗位, p.所属部门
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.档案编号 = '{archive_no}'
ORDER BY COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) DESC
LIMIT {limit}"""
    },
    {
        "id": "T22",
        "desc": "查询指定日期范围的带班记录（单日时 start=end）",
        "sql": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
WHERE b.带班日期 >= '{start_date}' AND b.带班日期 <= '{end_date}'
ORDER BY b.带班日期 DESC
LIMIT {limit}"""
    },
    {
        "id": "T23",
        "desc": "查询指定日期范围的跟班记录（单日时 start=end）",
        "sql": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
WHERE g.日期 >= '{start_date}' AND g.日期 <= '{end_date}'
ORDER BY g.日期 DESC
LIMIT {limit}"""
    },
    {
        "id": "T24",
        "desc": "统计人员信息表中指定职务的人数（例：网格长）",
        "sql": """SELECT 职务, COUNT(*) AS 人数
FROM 大桥局人员信息表
WHERE 职务 = '{duty}'
GROUP BY 职务"""
    },
    {
        "id": "T25",
        "desc": "统计人员信息表中正式员工的人数（字段：正式员工=1）",
        "sql": """SELECT COUNT(*) AS 正式员工数
FROM 大桥局人员信息表
WHERE 正式员工 = 1"""
    },
    {
        "id": "T26",
        "desc": "查询指定人员最近N条工作记录（带班+跟班合并，按时间倒序）",
        "sql": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
FROM (
  SELECT COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) AS ts,
         '带班' AS 类型,
         p1.姓名 AS 人员,
         b.带班作业工序及地点 AS 作业内容,
         b.带班日期 AS 发生日期
  FROM 带班作业记录表 AS b
  JOIN 大桥局人员信息表 AS p1 ON b.带班人员档案编号 = p1.档案编号
  WHERE p1.姓名 = '{person_name}'
  UNION ALL
  SELECT COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) AS ts,
         '跟班' AS 类型,
         p2.姓名 AS 人员,
         g.重点部位_关键工序_特殊时段情况 AS 作业内容,
         g.日期 AS 发生日期
  FROM 跟班作业记录表 AS g
  JOIN 大桥局人员信息表 AS p2 ON g.跟班人员档案编号 = p2.档案编号
  WHERE p2.姓名 = '{person_name}'
) AS t
ORDER BY ts DESC
LIMIT {limit}"""
    },
    {
        "id": "T27",
        "desc": "按档案编号查询最近N条工作记录（带班+跟班合并，按时间倒序）",
        "sql": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
FROM (
  SELECT COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) AS ts,
         '带班' AS 类型,
         p1.姓名 AS 人员,
         b.带班作业工序及地点 AS 作业内容,
         b.带班日期 AS 发生日期
  FROM 带班作业记录表 AS b
  JOIN 大桥局人员信息表 AS p1 ON b.带班人员档案编号 = p1.档案编号
  WHERE p1.档案编号 = '{archive_no}'
  UNION ALL
  SELECT COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) AS ts,
         '跟班' AS 类型,
         p2.姓名 AS 人员,
         g.重点部位_关键工序_特殊时段情况 AS 作业内容,
         g.日期 AS 发生日期
  FROM 跟班作业记录表 AS g
  JOIN 大桥局人员信息表 AS p2 ON g.跟班人员档案编号 = p2.档案编号
  WHERE p2.档案编号 = '{archive_no}'
) AS t
ORDER BY ts DESC
LIMIT {limit}"""
    },
]


class SQLTemplateManager:
    """SQL模板管理器"""

    @staticmethod
    def get_template(template_id: str) -> dict:
        """根据模板ID获取模板"""
        template = next((t for t in SQL_TEMPLATES if t["id"] == template_id), None)
        if not template:
            raise ValueError(f"未找到模板ID: {template_id}")
        return template

    @staticmethod
    def get_all_templates() -> list:
        """获取所有模板"""
        return SQL_TEMPLATES

    @staticmethod
    def get_template_descriptions() -> str:
        """获取所有模板的描述列表"""
        return "\n".join([
            f"- {t['id']}: {t['desc']}" for t in SQL_TEMPLATES
        ])


