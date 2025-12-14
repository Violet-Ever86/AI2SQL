import re
from typing import Sequence


class SQLValidator:
    """SQL验证器类，负责验证SQL语句的安全性"""

    @staticmethod
    def validate_sql(sql: str, allowed_tables: Sequence[str]) -> bool:
        """验证SQL语句是否安全"""
        sql_low = sql.lower().strip()
        if not sql_low.startswith("select"):
            return False
        if ";" in sql_low:
            return False
        if any(bad in sql_low for bad in ["insert ", "update ", "delete ", "drop ", "truncate ", "alter "]):
            return False
        # 可选：基于表名白名单的简单检查
        if allowed_tables:
            # 兼容中文表名：\u4e00-\u9fa5
            pattern = r"from\s+([`\w\u4e00-\u9fa5]+)"
            tables = re.findall(pattern, sql_low, flags=re.I)
            for t in tables:
                t_clean = t.replace("`", "")
                if t_clean not in [x.lower() for x in allowed_tables]:
                    return False
        return True


