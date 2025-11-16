# Restaurant-Agent API 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，填入你的 API Key：

```
ALIYUN_API_KEY=sk-your-api-key-here
ALIYUN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIYUN_MODEL=qwen-plus
GAODE_API_KEY=your-gaode-api-key-here
DEFAULT_CITY=北京
DEFAULT_LOCATION=116.4074,39.9042
```

### 3. 启动服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 `http://localhost:8000` 启动

## API 端点

### 1. 健康检查

**请求：**
```
GET /health
```

**响应：**
```json
{
    "status": "ok",
    "message": "Restaurant-Agent 服务正常运行"
}
```

---

### 2. 获取 Agent 信息

**请求：**
```
GET /api/info
```

**响应：**
```json
{
    "name": "Restaurant-Agent",
    "version": "1.0.0",
    "description": "智能美食推荐 Agent，支持场景识别、条件筛选、结果排序",
    "features": [
        "城市位置解析",
        "餐厅场景识别",
        "价格/评分筛选",
        "智能推荐排序"
    ]
}
```

---

### 3. 推荐餐厅（核心接口）

**请求：**
```
POST /api/recommend
Content-Type: application/json

{
    "query": "我在北京想吃川菜，有没有推荐？价格在100元以下"
}
```

**响应：**
```json
{
    "success": true,
    "message": "推荐成功",
    "data": {
        "query": "我在北京想吃川菜，有没有推荐？价格在100元以下",
        "scenario": "中餐厅-四川菜(川菜)",
        "types": "050117",
        "city": "北京",
        "location": "116.407387,39.904179",
        "filters_applied": {
            "price_range": {
                "min": 0,
                "max": 100
            }
        },
        "total_found": 50,
        "recommendation_count": 5,
        "recommendations": [
            {
                "name": "川菜馆1",
                "address": "北京市朝阳区xxx",
                "location": "116.407387,39.904179",
                "telephone": "010-12345678",
                "type": "050117",
                "rating": "4.5",
                "cost": "85"
            },
            {
                "name": "川菜馆2",
                "address": "北京市朝阳区yyy",
                "location": "116.407388,39.904180",
                "telephone": "010-87654321",
                "type": "050117",
                "rating": "4.3",
                "cost": "90"
            }
        ],
        "errors": []
    }
}
```

---

## 使用示例

### Python 客户端

```python
import requests
import json

# API 地址
BASE_URL = "http://localhost:8000"

# 推荐请求
response = requests.post(
    f"{BASE_URL}/api/recommend",
    json={"query": "我在北京想吃川菜，有没有推荐？价格在100元以下"}
)

result = response.json()

if result["success"]:
    data = result["data"]
    print(f"城市: {data['city']}")
    print(f"场景: {data['scenario']}")
    print(f"找到 {data['total_found']} 条结果，推荐 {data['recommendation_count']} 家")
    
    for i, restaurant in enumerate(data["recommendations"], 1):
        print(f"\n{i}. {restaurant['name']}")
        print(f"   地址: {restaurant['address']}")
        print(f"   电话: {restaurant['telephone']}")
        print(f"   评分: {restaurant['rating']}")
        print(f"   人均: {restaurant['cost']} 元")
else:
    print(f"推荐失败: {result['message']}")
```

### JavaScript/TypeScript 客户端

```javascript
// 推荐请求
const response = await fetch('http://localhost:8000/api/recommend', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        query: '我在北京想吃川菜，有没有推荐？价格在100元以下'
    })
});

const result = await response.json();

if (result.success) {
    const data = result.data;
    console.log(`城市: ${data.city}`);
    console.log(`场景: ${data.scenario}`);
    console.log(`找到 ${data.total_found} 条结果，推荐 ${data.recommendation_count} 家`);
    
    data.recommendations.forEach((restaurant, index) => {
        console.log(`\n${index + 1}. ${restaurant.name}`);
        console.log(`   地址: ${restaurant.address}`);
        console.log(`   电话: ${restaurant.telephone}`);
        console.log(`   评分: ${restaurant.rating}`);
        console.log(`   人均: ${restaurant.cost} 元`);
    });
} else {
    console.log(`推荐失败: ${result.message}`);
}
```

### cURL 请求

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "我在北京想吃川菜，有没有推荐？价格在100元以下"}'
```

---

## 交互式 API 文档

启动服务后，可以访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 错误处理

### 缺少必要参数

**请求：**
```json
{}
```

**响应：**
```json
{
    "success": false,
    "message": "缺少必要参数: query",
    "data": null
}
```

### Query 为空

**请求：**
```json
{"query": ""}
```

**响应：**
```json
{
    "success": false,
    "message": "query 不能为空",
    "data": null
}
```

### 推荐失败

**响应：**
```json
{
    "success": false,
    "message": "推荐失败: 具体错误信息",
    "data": null
}
```

---

## 性能考虑

- 首次请求可能需要 5-10 秒（LLM 推理时间）
- 建议添加请求超时设置（30 秒以上）
- 可以使用消息队列（如 Celery）处理异步推荐

---

## 常见问题

### Q: 为什么推荐结果为空？

A: 可能原因：
1. API Key 无效或配额不足
2. 城市名称不被识别
3. 搜索关键词太具体

### Q: 如何提高推荐准确度？

A: 
1. 提供更详细的 query（包括城市、菜系、价格等）
2. 确保 API Key 有足够配额
3. 检查网络连接

### Q: 支持哪些城市？

A: 支持高德地图覆盖的所有城市，包括但不限于：
- 北京、上海、广州、深圳
- 杭州、南京、武汉、成都
- 西安、重庆、天津、苏州
- 等等

---

## 部署建议

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
docker build -t restaurant-agent .
docker run -p 8000:8000 --env-file .env restaurant-agent
```

### 生产环境建议

1. 使用 Gunicorn + Uvicorn：
   ```bash
   gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```

2. 使用 Nginx 反向代理

3. 添加请求日志和监控

4. 配置速率限制防止滥用

---

## 许可证

MIT
