"""SQL字段替换器，用于将schema中的字段名替换为数据库中的实际字段名"""

import re
from typing import Dict


class SQLFieldReplacer:
    """SQL字段替换器类，负责将schema中的字段名替换为数据库实际字段名"""
    
    # 字段替换字典：key为schema中的字段名，value为数据库中的实际字段名
    FIELD_REPLACEMENT_MAP = {
        "带班人员档案编号": "带班人员",
        "带班领导档案编号": "带班领导",
        "管控责任人档案编号": "管控责任人"
    }
    
    @classmethod
    def replace_fields(cls, sql: str) -> str:
        """
        替换SQL中的字段名
        
        Args:
            sql: 原始SQL语句
            
        Returns:
            替换后的SQL语句
        """
        if not sql:
            return sql
        
        result_sql = sql
        
        # 按照字段名长度从长到短排序，避免短字段名被错误替换
        # 例如："带班人员档案编号" 应该在 "带班人员" 之前处理
        sorted_replacements = sorted(
            cls.FIELD_REPLACEMENT_MAP.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for schema_field, db_field in sorted_replacements:
            # 使用正则表达式进行精确替换，确保只替换字段名，不替换其他部分
            # 匹配模式：表名.字段名 或 字段名（在SELECT、WHERE、JOIN、ORDER BY等位置）
            
            # 1. 匹配 "表名.字段名" 格式（带或不带反引号，支持中文表名和字段名）
            # 匹配：带班作业记录表.带班人员档案编号 或 `带班作业记录表`.`带班人员档案编号`
            table_field_pattern = rf"([`\w\u4e00-\u9fa5]+)\.{re.escape(schema_field)}"
            result_sql = re.sub(
                table_field_pattern,
                rf"\1.{db_field}",
                result_sql,
                flags=re.IGNORECASE
            )
            
            # 2. 匹配单独的字段名（在SELECT、WHERE、JOIN、ORDER BY等位置）
            # 使用单词边界确保精确匹配，但要注意中文字符的边界处理
            # 对于中文字段名，我们需要匹配前后不是中文字符、字母、数字、下划线的位置
            # 或者使用更简单的方法：匹配前后是空格、逗号、等号、括号等的位置
            standalone_pattern = rf"(?<![`\w\u4e00-\u9fa5]){re.escape(schema_field)}(?![`\w\u4e00-\u9fa5])"
            result_sql = re.sub(standalone_pattern, db_field, result_sql, flags=re.IGNORECASE)
        
        return result_sql
    
    @classmethod
    def add_replacement(cls, schema_field: str, db_field: str):
        """
        添加新的字段替换规则
        
        Args:
            schema_field: schema中的字段名
            db_field: 数据库中的实际字段名
        """
        cls.FIELD_REPLACEMENT_MAP[schema_field] = db_field
    
    @classmethod
    def get_replacements(cls) -> Dict[str, str]:
        """
        获取所有字段替换规则
        
        Returns:
            字段替换字典
        """
        return cls.FIELD_REPLACEMENT_MAP.copy()

