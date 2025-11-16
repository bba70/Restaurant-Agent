"""
诊断脚本 - 检查 .env 文件是否被正确加载
"""
import os
from dotenv import load_dotenv

print("=" * 80)
print("环境变量诊断")
print("=" * 80)

# 方案1：检查 .env 文件是否存在
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"\n1. .env 文件路径: {env_path}")
print(f"   文件是否存在: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print(f"   文件大小: {os.path.getsize(env_path)} 字节")

# 方案2：加载 .env 文件
print(f"\n2. 加载 .env 文件...")
load_dotenv(dotenv_path=env_path, verbose=True)

# 方案3：检查环境变量
print(f"\n3. 环境变量值:")
print(f"   ALIYUN_API_KEY: {os.getenv('ALIYUN_API_KEY', '【未设置】')}")
print(f"   ALIYUN_BASE_URL: {os.getenv('ALIYUN_BASE_URL', '【未设置】')}")
print(f"   ALIYUN_MODEL: {os.getenv('ALIYUN_MODEL', '【未设置】')}")
print(f"   GAODE_API_KEY: {os.getenv('GAODE_API_KEY', '【未设置】')}")
print(f"   DEFAULT_CITY: {os.getenv('DEFAULT_CITY', '【未设置】')}")
print(f"   DEFAULT_LOCATION: {os.getenv('DEFAULT_LOCATION', '【未设置】')}")

# 方案4：检查 API Key 是否有效
print(f"\n4. API Key 有效性检查:")
aliyun_key = os.getenv('ALIYUN_API_KEY', '')
gaode_key = os.getenv('GAODE_API_KEY', '')

if aliyun_key and aliyun_key.startswith('sk-'):
    print(f"   ✅ ALIYUN_API_KEY 格式正确（以 sk- 开头）")
elif aliyun_key:
    print(f"   ⚠️  ALIYUN_API_KEY 格式可能不对（不以 sk- 开头）")
else:
    print(f"   ❌ ALIYUN_API_KEY 为空")

if gaode_key:
    print(f"   ✅ GAODE_API_KEY 已设置")
else:
    print(f"   ❌ GAODE_API_KEY 为空")

print("\n" + "=" * 80)
