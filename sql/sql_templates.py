"""SQL模板定义和管理模块"""

from sql.sql_template_sql import SQL_TEMPLATE_SQL

# SQL 模板定义：每个模板包含ID、描述、SQL模板（用 {参数} 占位）
SQL_TEMPLATES = [
    # 通用工作查询典型模板（1：带班；2：跟班；3：带班+跟班）
    {
        "id": "M1",
        "desc": "模板1：查询指定人员的带班记录（通过姓名，按时间倒序，限制条数）",
        "sql": SQL_TEMPLATE_SQL["M1"],
    },
    {
        "id": "M2",
        "desc": "模板2：查询指定人员的跟班记录（通过姓名，按时间倒序，限制条数）",
        "sql": SQL_TEMPLATE_SQL["M2"],
    },
    {
        "id": "M3",
        "desc": "模板3：查询指定人员的带班+跟班工作记录（通过姓名，合并结果按时间倒序）",
        "sql": SQL_TEMPLATE_SQL["M3"],
    },
    {
        "id": "M4",
        "desc": "查询人员信息表中某人的详细信息（通过姓名）",
        "sql": SQL_TEMPLATE_SQL["M4"],
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


