"""SQL模板的SQL语句映射表。"""

# 每个模板ID对应的原始SQL字符串
SQL_TEMPLATE_SQL = {
    "T1": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}'
ORDER BY COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) DESC
LIMIT {limit}""",

    "T2": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}'
ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC
LIMIT {limit}""",

    "T4": """SELECT 带班人员, 带班作业工序及地点, 带班日期, 带班开始时间, 带班结束时间
FROM 带班作业记录表
ORDER BY COALESCE(FGC_CreateDate, 带班日期, FGC_LastModifyDate) DESC
LIMIT {limit}""",

    "T5": """SELECT 跟班人员, 重点部位_关键工序_特殊时段情况, 日期, 班组
FROM 跟班作业记录表
ORDER BY COALESCE(FGC_CreateDate, 日期, FGC_LastModifyDate) DESC
LIMIT {limit}""",

    "T6": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
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
LIMIT {limit}""",

    "T7": """SELECT 日期, 班组, 重点部位_关键工序_特殊时段情况, 跟班人员, 跟班人员档案编号
FROM 跟班作业记录表
WHERE 跟班人员档案编号 = '{archive_no}'
ORDER BY COALESCE(FGC_CreateDate, 日期, FGC_LastModifyDate) DESC
LIMIT {limit}""",

    "T8": """SELECT 带班人员, 带班作业工序及地点, 带班日期, 带班开始时间, 带班结束时间
FROM 带班作业记录表
WHERE 带班日期 >= '{start_date}' AND 带班日期 <= '{end_date}'
ORDER BY 带班日期 DESC
LIMIT {limit}""",

    "T9": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND b.带班日期 = '{target_date}'
ORDER BY b.带班开始时间
LIMIT {limit}""",

    "T10": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND b.带班日期 >= '{start_date}' AND b.带班日期 <= '{end_date}'
ORDER BY b.带班日期 DESC
LIMIT {limit}""",

    "T11": """SELECT 档案编号, 姓名, 岗位, 职务, 手机号, 状态, 所属部门, 所属项目
FROM 大桥局人员信息表
WHERE 姓名 = '{person_name}'
LIMIT 1""",

    "T12": """SELECT COUNT(*) AS 人员总数
FROM 大桥局人员信息表""",

    "T13": """SELECT 状态, COUNT(*) AS 人数
FROM 大桥局人员信息表
WHERE 状态 = '{status}'
GROUP BY 状态""",

    "T15": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND g.日期 = '{target_date}'
ORDER BY g.日期
LIMIT {limit}""",

    "T16": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
WHERE p.姓名 = '{person_name}' AND g.日期 >= '{start_date}' AND g.日期 <= '{end_date}'
ORDER BY g.日期 DESC
LIMIT {limit}""",

    "T20": """SELECT 档案编号, 姓名, 岗位, 职务, 手机号, 状态, 所属部门, 所属项目
FROM 大桥局人员信息表
WHERE 手机号 = '{phone}'
LIMIT 1""",

    "T21": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间,
       p.姓名, p.手机号, p.岗位, p.所属部门
FROM 带班作业记录表 AS b
JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
WHERE p.档案编号 = '{archive_no}'
ORDER BY COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) DESC
LIMIT {limit}""",

    "T22": """SELECT b.带班日期, b.带班作业工序及地点, b.带班开始时间, b.带班结束时间
FROM 带班作业记录表 AS b
WHERE b.带班日期 >= '{start_date}' AND b.带班日期 <= '{end_date}'
ORDER BY b.带班日期 DESC
LIMIT {limit}""",

    "T23": """SELECT g.日期, g.班组, g.重点部位_关键工序_特殊时段情况, g.跟班人员, g.跟班人员档案编号
FROM 跟班作业记录表 AS g
WHERE g.日期 >= '{start_date}' AND g.日期 <= '{end_date}'
ORDER BY g.日期 DESC
LIMIT {limit}""",

    "T24": """SELECT 职务, COUNT(*) AS 人数
FROM 大桥局人员信息表
WHERE 职务 = '{duty}'
GROUP BY 职务""",

    "T25": """SELECT COUNT(*) AS 正式员工数
FROM 大桥局人员信息表
WHERE 正式员工 = 1""",

    "T26": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
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

    "T27": """SELECT ts AS 时间, 类型, 人员, 作业内容, 发生日期
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
  JOIN 大桥局人员信息表 AS p2
    ON (g.跟班人员档案编号 = p2.档案编号 OR g.跟班人员 = p2.姓名)
  WHERE p2.档案编号 = '{archive_no}'
) AS t
ORDER BY ts DESC
LIMIT {limit}""",
}


