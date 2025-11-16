"""
Restaurant-Agent 后端接口
使用 FastAPI 框架暴露 Agent 功能
"""
import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from plann_and_execute.agent import graph

# 初始化 FastAPI 应用
app = FastAPI(
    title="Restaurant-Agent API",
    description="智能美食推荐 Agent",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 请求模型
class RecommendRequest(BaseModel):
    """推荐请求模型"""
    query: str


# 响应模型
class Restaurant(BaseModel):
    """餐厅信息"""
    name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    telephone: Optional[str] = None
    type: Optional[str] = None
    rating: Optional[str] = None
    cost: Optional[str] = None


class RecommendResponse(BaseModel):
    """推荐响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    返回:
        - status: 服务状态
        - message: 状态信息
    """
    return {
        "status": "ok",
        "message": "Restaurant-Agent 服务正常运行"
    }


@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend_restaurants(request: RecommendRequest):
    """
    推荐餐厅接口
    
    请求体:
    ```json
    {
        "query": "我在北京想吃川菜，有没有推荐？价格在100元以下"
    }
    ```
    
    响应:
    ```json
    {
        "success": true,
        "message": "推荐成功",
        "data": {
            "query": "用户查询",
            "scenario": "场景",
            "types": "高德API类型码",
            "city": "城市",
            "location": "经纬度",
            "filters_applied": {...},
            "total_found": 100,
            "recommendation_count": 5,
            "recommendations": [
                {
                    "name": "餐厅名称",
                    "address": "地址",
                    "location": "经纬度",
                    "telephone": "电话",
                    "type": "类型",
                    "rating": "评分",
                    "cost": "人均消费"
                }
            ],
            "errors": []
        }
    }
    ```
    """
    try:
        query = request.query.strip()
        
        if not query:
            raise HTTPException(status_code=400, detail="query 不能为空")
        
        logger.info(f"收到推荐请求: {query}")
        
        # 构建初始状态
        initial_state = {
            "query": query,
            "replan_count": 0,
            "error_info": None,
            "past_plans": [],
        }
        
        # 调用 Agent
        logger.info("开始执行 Agent...")
        final_state = graph.invoke(initial_state)
        
        # 解析结果
        final_result_str = final_state.get("final_result", "{}")
        
        try:
            final_result = json.loads(final_result_str)
        except json.JSONDecodeError:
            logger.error(f"JSON 解析失败: {final_result_str}")
            final_result = {
                "query": query,
                "error": "结果解析失败"
            }
        
        logger.info(f"Agent 执行完成，找到 {final_result.get('recommendation_count', 0)} 条推荐")
        
        return RecommendResponse(
            success=True,
            message="推荐成功",
            data=final_result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"推荐失败: {str(e)}", exc_info=True)
        return RecommendResponse(
            success=False,
            message=f"推荐失败: {str(e)}",
            data=None
        )


@app.get("/api/info")
async def get_info():
    """
    获取 Agent 信息
    
    返回:
        - name: Agent 名称
        - version: 版本号
        - description: 描述
    """
    return {
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
