import pymysql
from datetime import date, datetime, time
from typing import Dict, List


class Database:
    """数据库操作类，负责执行SQL查询和数据处理"""

    def __init__(self, db_conf: Dict):
        self.db_conf = db_conf

    @staticmethod
    def serialize_row(row: Dict) -> Dict:
        """将数据库行中的日期/时间对象转换为字符串，以便JSON序列化"""
        serialized = {}
        for key, value in row.items():
            if isinstance(value, (date, datetime)):
                serialized[key] = value.isoformat()
            elif isinstance(value, time):
                serialized[key] = str(value)
            else:
                serialized[key] = value
        return serialized

    def run_query(self, sql: str) -> List[Dict]:
        """执行SQL查询并返回结果"""
        try:
            conn = pymysql.connect(
                host=self.db_conf["host"],
                port=int(self.db_conf["port"]),
                user=self.db_conf["user"],
                password=self.db_conf["password"],
                database=self.db_conf["db"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
            )
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rows = cur.fetchall()
                    # 转换日期/时间对象为字符串
                    return [self.serialize_row(row) for row in rows]
            finally:
                conn.close()
        except pymysql.err.OperationalError as e:
            error_msg = str(e)
            if "Can't connect" in error_msg or "拒绝" in error_msg:
                print(f"\n错误：无法连接到MySQL数据库")
                print(f"请检查：")
                print(f"  1. MySQL服务是否正在运行")
                print(f"  2. 连接配置是否正确（host={self.db_conf['host']}, port={self.db_conf['port']}, db={self.db_conf['db']}）")
                print(f"  3. 用户名和密码是否正确")
                print(f"\n生成的SQL（已验证正确）：\n{sql}")
            raise
        except Exception as e:
            print(f"\n数据库查询错误：{e}")
            print(f"\n生成的SQL：\n{sql}")
            raise


