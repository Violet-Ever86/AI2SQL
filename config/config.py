import argparse
import os
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description='NL -> SQL -> MySQL -> Summary demo')

# Schema文件路径
parser.add_argument('--schema-path', default='./data/schema_prompt.txt', help='Schema文件路径')

# 数据库配置
parser.add_argument('--db-host', default=os.getenv('DB_HOST', '10.84.11.214'), help='数据库主机地址')
parser.add_argument('--db-port', type=int, default=int(os.getenv('DB_PORT', '3306')), help='数据库端口')
parser.add_argument('--db-user', default=os.getenv('DB_USER', 'Lmodel'), help='数据库用户名')
parser.add_argument('--db-password', default=os.getenv('DB_PASSWORD', 'dnDNn32_mdn133*'), help='数据库密码')
parser.add_argument('--db-name', default=os.getenv('DB_NAME', 'aqcts'), help='数据库名称')

# LLM配置
parser.add_argument('--llm-endpoint', default=os.getenv('LLM_ENDPOINT', 'https://ollama.com'), help='LLM API端点')
parser.add_argument('--llm-model',   default=os.getenv('LLM_MODEL', 'gpt-oss:120b'), help='LLM模型名称')
parser.add_argument('--llm-api-key', default=os.getenv('LLM_API_KEY', '03d6ad60e0a7481f8051c03577dfd2ac.dybsRCxL0xS25kW1lx_lyVmw'), help='LLM API密钥')
parser.add_argument('--llm-api-type',default=os.getenv('LLM_API_TYPE', 'chat'), choices=['completion','chat'], help='LLM API类型')


# 业务参数
parser.add_argument('--question', '-q', type=str, help='自然语言问题')

params = parser.parse_args()

