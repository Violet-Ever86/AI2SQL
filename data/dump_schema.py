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
    "db": os.getenv("DB_NAME", "demo"),
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


def get_relationship_constraints():
    """返回关联关系与时间约定内容"""
    return """
关联关系与时间约定：
- 带班作业记录表.带班人员档案编号 与 大桥局人员信息表.档案编号 对应。
- 跟班作业记录表.跟班人员 与 大桥局人员信息表.姓名 对应。
- 带班作业记录表.联合带班人员档号 与 大桥局人员信息表.档案编号 对应。
- 跟班作业记录表.跟班人员档案编号 与 大桥局人员信息表.档案编号 对应。
- 若问题没指定时间范围，建议在 SQL 中按时间字段降序。
- 每日管控计划.ID 与 每日管控计划_子表.每日管控计划_ID 对应
- 每日管控计划_子表.工序id字符串 与 安全责任单元履职清单主表.ID 对应
- 每日管控计划.管控单元id 与 责任单元字典.ID 对应。
- 带班作业记录表.工单ID 与 每日管控计划.ID对应
- 带班作业记录表.工单子表ID 与 每日管控计划_子表.ID对应
- 跟班作业记录表.工单ID 与 每日管控计划.ID对应
- 跟班作业记录表.工单子表ID 与 每日管控计划_子表.ID对应
- 班前讲话班组字典.安全责任单元 与 责任单元字典.id 对应。
- 班前讲话班组字典.班组 与 跟班作业记录表.ID 对应
""".strip()


def main():
    parser = argparse.ArgumentParser(description="Dump MySQL schema to text")
    parser.add_argument("--out", "-o", type=str, default="./schema_prompt.txt", help="输出文件路径（默认: ./schema_prompt.txt）")
    parser.add_argument("--stdout", action="store_true", help="输出到标准输出而不是文件")
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

    # 添加关联关系与时间约定
    relationship_constraints = get_relationship_constraints()
    full_content = schema_str + "\n\n" + relationship_constraints
    
    if args.stdout:
        # 输出到标准输出
        print(full_content)
    else:
        # 写入文件（默认行为）
        # 获取绝对路径用于调试
        abs_path = os.path.abspath(args.out)
        sys.stderr.write(f"[dump_schema] 正在写入文件: {abs_path}\n")
        sys.stderr.write(f"[dump_schema] 文件大小: {len(full_content)} 字符, 行数: {full_content.count(chr(10)) + 1}\n")
        
        # 确保目录存在
        if os.path.dirname(args.out):
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
        
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        # 验证文件是否写入成功
        if os.path.exists(args.out):
            file_size = os.path.getsize(args.out)
            sys.stderr.write(f"[dump_schema] 文件写入成功！文件大小: {file_size} 字节\n")
        else:
            sys.stderr.write(f"[dump_schema] 警告：文件写入后不存在！\n")


if __name__ == "__main__":
    main()
