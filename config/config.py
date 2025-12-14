import argparse
import os
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description='NL -> SQL -> MySQL -> Summary demo')

# Schema文件路径
parser.add_argument('--schema-path', default='./data/schema_prompt.txt', help='Schema文件路径')

# 数据库配置
parser.add_argument('--db-host', default=os.getenv('DB_HOST', '127.0.0.1'), help='数据库主机地址')
parser.add_argument('--db-port', type=int, default=int(os.getenv('DB_PORT', '3306')), help='数据库端口')
parser.add_argument('--db-user', default=os.getenv('DB_USER', 'root'), help='数据库用户名')
parser.add_argument('--db-password', default=os.getenv('DB_PASSWORD', 'violet'), help='数据库密码')
parser.add_argument('--db-name', default=os.getenv('DB_NAME', 'test_db'), help='数据库名称')

# LLM配置
parser.add_argument('--llm-endpoint', default=os.getenv('LLM_ENDPOINT', 'http://10.79.79.242:11434'), help='LLM API端点')
parser.add_argument('--llm-model', default=os.getenv('LLM_MODEL', 'gpt-oss:120b-cloud'), help='LLM模型名称')
parser.add_argument('--llm-api-key', default=os.getenv('LLM_API_KEY', 'app-GjhXLg055szLhS3xjtXxvWLp'), help='LLM API密钥')
parser.add_argument('--llm-api-type', default=os.getenv('LLM_API_TYPE', 'completion'), choices=['completion', 'chat'], help='LLM API类型：completion 或 chat')

# 业务参数
parser.add_argument('--question', '-q', type=str, help='自然语言问题')

params = parser.parse_args()

