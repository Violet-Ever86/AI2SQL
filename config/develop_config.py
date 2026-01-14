import argparse

parser = argparse.ArgumentParser(description="开发环境参数配置")

# 数据库配置
parser.add_argument('--db_host', default='127.0.0.1', help='数据库主机地址')
parser.add_argument('--db_port', default=3306, help='数据库端口')
parser.add_argument('--db_user', default='root', help='数据库用户名')
parser.add_argument('--db_password', default='violet', help='数据库密码')
parser.add_argument('--db_name', default='test_db', help='数据库名称')

# LLM配置
parser.add_argument('--llm_endpoint', default='https://ollama.com', help='LLM API端点')
parser.add_argument('--llm_model',   default='gpt-oss:120b', help='LLM模型名称')
parser.add_argument('--llm_api_key', default='03d6ad60e0a7481f8051c03577dfd2ac.dybsRCxL0xS25kW1lx_lyVmw', help='LLM API密钥')
parser.add_argument('--llm_api_type',default='chat', choices=['completion','chat'], help='LLM API类型')
