tool_list = \
    {
        "select_templates":
            {
                "description": "当用户的问题能够匹配模板时，选择**一个**最匹配问题的模板",
                "parameters": {"template_id": "此处应为最匹配问题的模板id，例如 M1"}
            },
        "generate_sql":
            {
                "description": "当用户的问题不匹配模板时，**必须**参考sql生成规则自由生成sql",
                "parameters": {"sql": "此处应为生成的sql查询语句"}
            },
    }