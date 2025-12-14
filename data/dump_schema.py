import argparse
import os
import sys

import pymysql
from dotenv import load_dotenv

# Usage: python dump_schema.py > schema_prompt.txt
# Reads DB config from .env (same keys as main.py) and prints a human-friendly schema description.


load_dotenv()

DB_CONF = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "db": os.getenv("DB_NAME", "my_project"),
    "charset": "utf8mb4",
}


def normalize_type(mysql_type: str) -> str:
    """将MySQL类型转换为更通用的类型名称，便于LLM理解"""
    mysql_type_lower = mysql_type.lower()
    
    # 字符串类型
    if mysql_type_lower.startswith("varchar") or mysql_type_lower.startswith("char"):
        return "string"
    if mysql_type_lower.startswith("text"):
        return "text"
    
    # 数值类型
    if mysql_type_lower.startswith("int") or mysql_type_lower.startswith("tinyint") or \
       mysql_type_lower.startswith("smallint") or mysql_type_lower.startswith("bigint"):
        return "int"
    if mysql_type_lower.startswith("decimal") or mysql_type_lower.startswith("float") or \
       mysql_type_lower.startswith("double"):
        return "float"
    
    # 日期时间类型
    if mysql_type_lower.startswith("date"):
        return "date"
    if mysql_type_lower.startswith("datetime") or mysql_type_lower.startswith("timestamp"):
        return "datetime"
    if mysql_type_lower.startswith("time"):
        return "time"
    
    # 其他类型保持原样
    return mysql_type


def fetch_schema():
    try:
        conn = pymysql.connect(
            host=DB_CONF["host"],
            port=DB_CONF["port"],
            user=DB_CONF["user"],
            password=DB_CONF["password"],
            database="information_schema",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        sys.stderr.write(f"[dump_schema] 连接数据库失败: {e}\n")
        return ""

    try:
        with conn.cursor() as cur:
            # Fetch tables
            cur.execute(
                """
                SELECT table_name, table_comment
                FROM tables
                WHERE table_schema = %s
                ORDER BY table_name;
                """,
                (DB_CONF["db"],),
            )
            tables_raw = cur.fetchall()

            # Fetch columns
            cur.execute(
                """
                SELECT table_name, column_name, column_type, is_nullable,
                       column_key, column_default, extra, column_comment
                FROM columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position;
                """,
                (DB_CONF["db"],),
            )
            cols_raw = cur.fetchall()
    finally:
        conn.close()

    # Normalize keys to lowercase to avoid KeyError when driver returns uppercase
    def normalize(rows):
        normed = []
        for r in rows:
            normed.append({(k.lower() if isinstance(k, str) else k): v for k, v in r.items()})
        return normed

    tables = normalize(tables_raw)
    cols = normalize(cols_raw)

    # group columns by table
    table_cols = {}
    for c in cols:
        table_cols.setdefault(c["table_name"], []).append(c)

    lines = []
    for t in tables:
        tname = t["table_name"]
        tcomment = t.get("table_comment") or ""
        lines.append(f"表名: {tname}")
        if tcomment:
            lines.append(f"表备注: {tcomment}")
        lines.append("字段:")
        for c in table_cols.get(tname, []):
            cname = c["column_name"]
            ctype = normalize_type(c["column_type"])  # 转换为通用类型
            ccomment = c.get("column_comment") or ""

            # 只显示字段名和类型，去掉NULL/NOT NULL以节省token
            parts = [f"- {cname} ({ctype})"]
            if ccomment:
                parts.append(f": {ccomment}")
            lines.append("".join(parts))
        lines.append("")  # blank line between tables

    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description="Dump MySQL schema to text")
    parser.add_argument("--out", "-o", type=str, help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    schema_str = fetch_schema()
    if not schema_str:
        sys.stderr.write(
            "[dump_schema] 未获取到任何表结构，请检查：\n"
            f"- DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME 是否正确（当前 DB_NAME={DB_CONF['db']})\n"
            "- 数据库是否有表，或账号是否有访问 information_schema 权限\n"
        )
        sys.exit(1)

    # Ensure utf-8 output on Windows consoles
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(schema_str)
    else:
        print(schema_str)


if __name__ == "__main__":
    main()
