import argparse

parser = argparse.ArgumentParser(description="生产环境参数配置")

# 数据库配置
parser.add_argument('--db_host', default='10.84.11.214', help='数据库主机地址')
parser.add_argument('--db_port', type=int, default=3306, help='数据库端口')
parser.add_argument('--db_user', default='Lmodel', help='数据库用户名')
parser.add_argument('--db_password', default='dnDNn32_mdn133*', help='数据库密码')
parser.add_argument('--db_name', default='aqcts', help='数据库名称')

# 大模型配置
parser.add_argument('--llm_endpoint', default='https://ai-api.crec.cn/v1', help='LLM API端点')
parser.add_argument('--llm_model',   default='DeepSeek-V3.1:671B', help='LLM模型名称')
parser.add_argument('--llm_api_key', default='sk-ypyAh4NQw0DT95UGcHlRlHyDV76zKEmg8wZuXkNQpwV4V4LF', help='LLM API密钥')
parser.add_argument('--llm_api_type',default='chat', choices=['completion','chat'], help='LLM API类型')

