"""SQL模板的SQL语句映射表。"""

# 每个模板ID对应的原始SQL字符串（已精简为 M1~M4 四个）
SQL_TEMPLATE_SQL = {
    # M1：按姓名查询带班记录（只要日期和工序，按时间倒序，最多50条）
    "M1": """SELECT b.带班日期, b.带班作业工序及地点
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}'
ORDER BY COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) DESC
LIMIT {limit}""",

    # M2：按姓名查询跟班记录（只要日期和关键工序描述，按时间倒序，最多50条）
    "M2": """SELECT g.日期, g.重点部位_关键工序_特殊时段情况
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}'
ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC
LIMIT {limit}""",

    # M3：按姓名查询带班+跟班合并的工作记录（统一结构，按时间倒序，最多50条）
    "M3": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
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
  JOIN 大桥局人员信息表 AS p2
    ON (g.跟班人员档案编号 = p2.档案编号 OR g.跟班人员 = p2.姓名)
  WHERE p2.姓名 = '{person_name}'
) AS t
ORDER BY ts DESC
LIMIT {limit}""",

    # M4：按姓名查询人员详细信息
    "M4": """SELECT 档案编号, 姓名, 岗位, 职务, 手机号, 状态, 所属部门, 所属项目
FROM 大桥局人员信息表
WHERE 姓名 = '{person_name}'
LIMIT 1""",
}

