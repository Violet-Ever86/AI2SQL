import argparse
import os
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description='NL -> SQL -> MySQL -> Summary demo')

# Schema文件路径
parser.add_argument('--schema-path', default='./data/schema_prompt.txt', help='Schema文件路径')

# 环境参数
parser.add_argument('--env', default='development', choices=['development', 'production'], 
                    help='运行环境：development（开发环境）或 production（生产环境）')

# 业务参数
parser.add_argument('--question', '-q', type=str, help='自然语言问题')

params = parser.parse_args()

# 根据环境加载配置
if params.env == 'production':
    # 生产环境：从 production.env 文件加载配置
    production_env_path = os.path.join(os.path.dirname(__file__), 'production.env')
    if not os.path.exists(production_env_path):
        raise FileNotFoundError(
            f"错误：未找到生产环境配置文件 {production_env_path}。"
            f"请创建该文件并配置生产环境的相关参数。"
        )
    
    # 加载 production.env 文件
    load_dotenv(production_env_path)
    
    # 数据库配置（必须从 production.env 文件读取）
    params.db_host = os.getenv('DB_HOST')
    params.db_port = os.getenv('DB_PORT')
    params.db_user = os.getenv('DB_USER')
    params.db_password = os.getenv('DB_PASSWORD')
    params.db_name = os.getenv('DB_NAME')
    
    # LLM配置（必须从 production.env 文件读取）
    params.llm_endpoint = os.getenv('LLM_ENDPOINT')
    params.llm_model = os.getenv('LLM_MODEL')
    params.llm_api_key = os.getenv('LLM_API_KEY')
    params.llm_api_type = os.getenv('LLM_API_TYPE', 'chat')
    # 生产环境的额外模型ID
    params.llm_reasoner_model = os.getenv('LLM_REASONER_MODEL', 'deepseek-reasoner')
else:
    # 开发环境：使用默认配置
    params.db_host = os.getenv('DB_HOST', '127.0.0.1')
    params.db_port = int(os.getenv('DB_PORT', '3306'))
    params.db_user = os.getenv('DB_USER', 'root')
    params.db_password = os.getenv('DB_PASSWORD', '123456')
    params.db_name = os.getenv('DB_NAME', 'demo')
    
    params.llm_endpoint = os.getenv('LLM_ENDPOINT', 'https://ollama.com')
    params.llm_model = os.getenv('LLM_MODEL', 'gpt-oss:120b')
    params.llm_api_key = os.getenv('LLM_API_KEY', '03d6ad60e0a7481f8051c03577dfd2ac.dybsRCxL0xS25kW1lx_lyVmw')
    params.llm_api_type = os.getenv('LLM_API_TYPE', 'chat')
    # 开发环境可能不需要 reasoner_model，设为 None
    params.llm_reasoner_model = os.getenv('LLM_REASONER_MODEL', None)

