"""SQL模板定义和管理模块"""

from sql.sql_template_sql import SQL_TEMPLATE_SQL

# SQL 模板定义：每个模板包含ID、描述、SQL模板（用 {参数} 占位）
SQL_TEMPLATES = [
    {
        "id": "T1",
        "desc": "查询指定人员最近的带班记录（通过姓名）",
        "sql": SQL_TEMPLATE_SQL["T1"],
    },
    {
        "id": "T2",
        "desc": "查询指定人员最近的跟班记录（通过姓名，需关联人员表）",
        "sql": SQL_TEMPLATE_SQL["T2"],
    },
    {
        "id": "T4",
        "desc": "查询最近N条带班记录（不限人员）",
        "sql": SQL_TEMPLATE_SQL["T4"],
    },
    {
        "id": "T5",
        "desc": "查询最近N条跟班记录（不限人员）",
        "sql": SQL_TEMPLATE_SQL["T5"],
    },
    {
        "id": "T6",
        "desc": "查询最近N条工作记录（带班+跟班合并，不限人员）",
        "sql": SQL_TEMPLATE_SQL["T6"],
    },
    {
        "id": "T7",
        "desc": "按档案编号查询人员最近的跟班记录",
        "sql": SQL_TEMPLATE_SQL["T7"],
    },
    {
        "id": "T8",
        "desc": "查询指定日期范围的带班记录（不限人员）",
        "sql": SQL_TEMPLATE_SQL["T8"],
    },
    {
        "id": "T9",
        "desc": "查询指定人员在指定日期的带班记录（人员+日期）",
        "sql": SQL_TEMPLATE_SQL["T9"],
    },
    {
        "id": "T10",
        "desc": "查询指定人员在指定日期范围的带班记录（人员+日期范围）",
        "sql": SQL_TEMPLATE_SQL["T10"],
    },
    {
        "id": "T11",
        "desc": "查询人员信息表中某人的详细信息（通过姓名）",
        "sql": SQL_TEMPLATE_SQL["T11"],
    },
    {
        "id": "T12",
        "desc": "统计人员信息表的总人数",
        "sql": SQL_TEMPLATE_SQL["T12"],
    },
    {
        "id": "T13",
        "desc": "按状态统计人员数量（例如在职/离职/停职等）",
        "sql": SQL_TEMPLATE_SQL["T13"],
    },
    {
        "id": "T15",
        "desc": "查询指定人员在指定日期的跟班记录（人员+日期）",
        "sql": SQL_TEMPLATE_SQL["T15"],
    },
    {
        "id": "T16",
        "desc": "查询指定人员在指定日期范围的跟班记录（人员+日期范围）",
        "sql": SQL_TEMPLATE_SQL["T16"],
    },
    {
        "id": "T20",
        "desc": "按手机号查询人员详细信息",
        "sql": SQL_TEMPLATE_SQL["T20"],
    },
    {
        "id": "T21",
        "desc": "按档案编号查询最近的带班记录（含联系方式）",
        "sql": SQL_TEMPLATE_SQL["T21"],
    },
    {
        "id": "T22",
        "desc": "查询指定日期范围的带班记录（单日时 start=end）",
        "sql": SQL_TEMPLATE_SQL["T22"],
    },
    {
        "id": "T23",
        "desc": "查询指定日期范围的跟班记录（单日时 start=end）",
        "sql": SQL_TEMPLATE_SQL["T23"],
    },
    {
        "id": "T24",
        "desc": "统计人员信息表中指定职务的人数（例：网格长）",
        "sql": SQL_TEMPLATE_SQL["T24"],
    },
    {
        "id": "T25",
        "desc": "统计人员信息表中正式员工的人数（字段：正式员工=1）",
        "sql": SQL_TEMPLATE_SQL["T25"],
    },
    {
        "id": "T26",
        "desc": "查询指定人员最近N条工作记录（带班+跟班合并，按时间倒序）",
        "sql": SQL_TEMPLATE_SQL["T26"],
    },
    {
        "id": "T27",
        "desc": "按档案编号查询最近N条工作记录（带班+跟班合并，按时间倒序）",
        "sql": SQL_TEMPLATE_SQL["T27"],
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


