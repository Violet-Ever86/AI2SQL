SQL_DICT = {
    # M1：按姓名查询带班记录（只要日期和工序，按时间倒序）
    "M1": """SELECT b.带班日期, b.带班作业工序及地点
    FROM 带班作业记录表 AS b
    JOIN 大桥局人员信息表 AS p ON b.带班人员档案编号 = p.档案编号
    WHERE p.姓名 = '{person_name}'
    ORDER BY COALESCE(b.FGC_CreateDate, b.带班日期, b.FGC_LastModifyDate) DESC""",

    # M2：按姓名查询跟班记录（只要日期和关键工序描述，按时间倒序）
    "M2": """SELECT g.日期, g.重点部位_关键工序_特殊时段情况 
    FROM 跟班作业记录表 AS g
    JOIN 大桥局人员信息表 AS p ON g.跟班人员档案编号 = p.档案编号
    WHERE p.姓名 = '{person_name}'
    ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC""",

    # M3：按姓名查询带班+跟班合并的工作记录（统一结构，按时间倒序）
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
    ORDER BY ts DESC""",

    # M4：按姓名查询人员详细信息
    "M4": """SELECT 档案编号, 姓名, 岗位, 职务, 手机号, 状态, 所属部门, 所属项目
    FROM 大桥局人员信息表
    WHERE 姓名 = '{person_name}'""",

    # M5：按班组名称查询跟班记录（只要日期和关键工序描述，按时间倒序）
    "M5": """SELECT g.日期, g.重点部位_关键工序_特殊时段情况
    FROM 跟班作业记录表 AS g
    JOIN 班前讲话班组字典 AS d ON g.班组 = d.班组ID
    WHERE d.班组 = '{team_name}'
    ORDER BY COALESCE(g.FGC_CreateDate, g.日期, g.FGC_LastModifyDate) DESC""",

        # M6：按管控计划内容查询状态（内容可能在主表的施工计划作业内容或子表的分项名称中，按时间倒序）
    "M6": """SELECT 
        p.计划日期,
        p.管控责任人档案编号,
        p.施工计划作业内容,
        p.状态 AS 计划状态,
        s.分项名称,
        s.工序名称,
        s.风险研判,
        s.管控措施,
        s.关键工序,
        s.领导带班,
        s.跟班作业,
        leader.姓名 AS 带班领导姓名,
        follower.姓名 AS 跟班人员姓名,
        duty.带班作业工序及地点,
        duty.带班期间工作内容,
        duty.带班注意事项及要求,
        follow.安全质量__管控情况__,
        follow.过程偏离或达不到安全质量目标情况及处理措施,
        follow.状态 AS 跟班记录状态,
        duty.状态 AS 带班记录状态
    FROM 每日管控计划 AS p
    LEFT JOIN 责任单元字典 AS ru ON p.管控单元id = ru.ID
    LEFT JOIN 每日管控计划_子表 AS s ON p.ID = s.每日管控计划_ID
    LEFT JOIN 大桥局人员信息表 AS leader ON s.带班领导档案 = leader.档案编号
    LEFT JOIN 大桥局人员信息表 AS follower ON s.跟班人档案 = follower.档案编号
    LEFT JOIN 带班作业记录表 AS duty ON s.ID = duty.工单子表ID 
        AND DATE(duty.带班日期) = DATE(p.计划日期)
    LEFT JOIN 跟班作业记录表 AS follow ON s.ID = follow.工单子表ID 
        AND DATE(follow.日期) = DATE(p.计划日期)
    WHERE p.计划日期 = '{date}'
        AND ru.责任单元名称 LIKE '%{unit_name}%'
    ORDER BY s.ID, p.ID""",
}

"""SQL模板定义和管理模块"""

# SQL 模板定义：每个模板包含ID、描述、SQL模板（用 {参数} 占位）、必需参数列表
SQL_TEMPLATES = {
    "M1": {
        "desc": "通过姓名查询指定人员的带班记录（包括带班日期、内容和地点）",
        "required_params": ["person_name"],
    },
    "M2": {
        "desc": "通过姓名查询指定人员的跟班记录（包括跟班日期、内容和地点）",
        "required_params": ["person_name"],
    },
    "M3": {
        "desc": "通过姓名查询指定人员的带班+跟班工作记录（包括跟带班日期、内容和地点）",
        "required_params": ["person_name"],  # 必需参数列表
    },
    "M4": {
        "desc": "通过姓名查询人员信息表中某人的详细信息（所有已有信息）",
        "required_params": ["person_name"],
    },
    "M5": {
        "desc": "通过班组名称查询指定班组的跟班记录",
        "required_params": ["team_name"],
    },
    "M6": {
        "desc": "模板6：通过日期和单元名称（即地点）查询管控计划的具体内容",
        "required_params": ["date", "unit_name"],
    },
}



class SQLTemplateManager:
    """SQL模板管理器"""

    @staticmethod
    def get_template(template_id: str) -> dict:
        """根据模板ID获取模板"""
        template = {"decs": SQL_TEMPLATES[template_id]["desc"], "sql": SQL_DICT[template_id]}
        if not template:
            raise ValueError(f"未找到模板ID: {template_id}")
        return template

    @staticmethod
    def get_template_descriptions() -> str:
        """获取所有模板的描述列表"""
        return "\n".join([
            f"- {k}: {v['desc']}" for k, v in SQL_TEMPLATES.items()
        ])


