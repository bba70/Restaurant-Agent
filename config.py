"""
配置管理模块 - 从 .env 文件读取配置
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（指定绝对路径确保能找到）
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, verbose=True)

# Aliyun DashScope 配置
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY", "")
ALIYUN_BASE_URL = os.getenv("ALIYUN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
ALIYUN_MODEL = os.getenv("ALIYUN_MODEL", "qwen-plus")


# Gaode API 配置
GAODE_API_KEY = os.getenv("GAODE_API_KEY", "")

# 默认位置配置
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "北京")
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "116.4074,39.9042")

# 验证必要的配置（仅在实际使用时检查，允许测试时为空）
def _validate_api_keys():
    """验证 API Key 是否已配置"""
    if not ALIYUN_API_KEY or ALIYUN_API_KEY == "your-api-key-here":
        print("⚠️  警告: ALIYUN_API_KEY 未配置或使用默认值")
    if not GAODE_API_KEY or GAODE_API_KEY == "your-gaode-api-key-here":
        print("⚠️  警告: GAODE_API_KEY 未配置或使用默认值")
