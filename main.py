"""
Restaurant-Agent 后端接口
使用 FastAPI 框架暴露 Agent 功能
"""
import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

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

# 文件路径
FRONTEND_DIR = Path("web/dist")
FRONTEND_INDEX = FRONTEND_DIR / "index.html"


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


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """
    根路由：返回前端 index.html
    """
    if not FRONTEND_INDEX.exists():
        raise HTTPException(
            status_code=404, 
            detail="Frontend not built. Please run 'npm run build' in the web directory."
        )
    return FileResponse(FRONTEND_INDEX)


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
            "search_mode": "single | intersection",
            "fallback": null,
            "locations": [{"name": "地点名", "lnglat": "116.xxx,39.xxx"}],
            "location_count": 1,
            "total_found": 100,
            "recommendation_count_hard": 5,
            "recommendation_count_soft": 5,
            "recommendations_hard": [...],
            "recommendations_soft": [...],
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
        # 注意: 这里的 graph.invoke 依赖您的 plann_and_execute 模块，假设它是可用的
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
        
        hard_count = final_result.get('recommendation_count_hard', final_result.get('recommendation_count', 0))
        soft_count = final_result.get('recommendation_count_soft', 0)
        logger.info(f"Agent 执行完成，hard: {hard_count} 条, soft: {soft_count} 条推荐")
        
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
        "version": "2.0.0",
        "description": "智能美食推荐 Agent，支持多地点等距搜索、场景识别、条件筛选、均衡度排序",
        "features": [
            "多地点解析与地理编码",
            "搜索意图分类（单点/等距/沿途/对比）",
            "多点等距搜索与严格交集匹配",
            "降级中点搜索策略",
            "餐厅场景识别",
            "价格/评分筛选",
            "均衡度双模式排序（hard + soft）",
        ]
    }


# 挂载静态文件目录
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="static-assets")


# SPA fallback 路由：非 API 路径的 GET 请求返回 index.html
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(request: Request, full_path: str):
    """
    SPA fallback：所有非 API 路径返回 index.html，由前端路由处理
    """
    # 如果是 API 路径，返回 404
    if full_path.startswith("api/") or full_path == "health":
        raise HTTPException(status_code=404, detail="Not found")
    
    # 如果前端文件存在，返回 index.html
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    
    raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )