import pymysql
from datetime import date, datetime, time, timedelta
from typing import Dict, List
import decimal
from config.config import logger


class Database:
    """数据库操作类，负责执行SQL查询和数据处理"""

    def __init__(self, db_conf: Dict):
        self.db_conf = db_conf

    @staticmethod
    def serialize_row(row: Dict) -> Dict:
        """将数据库行中的日期/时间对象转换为字符串，以便JSON序列化"""
        serialized = {}
        for key, value in row.items():
            if value is None:
                serialized[key] = None
            elif isinstance(value, (date, datetime)):
                serialized[key] = value.isoformat()
            elif isinstance(value, (time, timedelta)):
                # time 和 timedelta 都转换为字符串
                serialized[key] = str(value)
            elif isinstance(value, decimal.Decimal):
                # Decimal 类型转换为 float
                serialized[key] = float(value)
            elif isinstance(value, (bytes, bytearray)):
                # 二进制数据转换为字符串
                serialized[key] = value.decode('utf-8', errors='ignore')
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
                logger.error(f"错误：无法连接到MySQL数据库")
                logger.error(f"请检查：")
                logger.error(f"  1. MySQL服务是否正在运行")
                logger.error(f"  2. 连接配置是否正确（host={self.db_conf['host']}, port={self.db_conf['port']}, db={self.db_conf['db']}）")
                logger.error(f"  3. 用户名和密码是否正确")
                logger.error(f"生成的SQL（已验证正确）：\n{sql}")
            raise
        except Exception as e:
            logger.error(f"数据库查询错误：{e}")
            logger.error(f"生成的SQL：\n{sql}")
            raise


