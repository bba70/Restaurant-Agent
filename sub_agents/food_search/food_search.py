import os
import requests
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from config import GAODE_API_KEY

class FoodSearchState(TypedDict):
    search_criteria: Dict[str, Any]

    search_results: List[Dict[str, Any]]

    error_messages: List[str]

def gaode_poi_search_node(state: FoodSearchState) -> FoodSearchState:
    '''
    高德地图POI搜索节点
    '''

    print("--- [Agent] 进入 高德美食搜索Agent ---")

    if not GAODE_API_KEY:
        raise EnvironmentError("错误：GAODE_API_KEY 未设置。")
    
    criteria = state.get("search_criteria")
    if not criteria or "keywords" not in criteria or "location" not in criteria:
        error_msg = "输入错误：search_criteria 必须包含 'keywords' 和 'location'。"
        print(f"  < {error_msg}")
        # 追加错误并立即返回
        state['error_messages'].append(error_msg)
        return state
    
    offset = int(criteria.get("offset", 20))
    pages = int(criteria.get("pages", 5))
    api_url = "https://restapi.amap.com/v3/place/around"
    all_results: List[Dict[str, Any]] = []
    
    try:
        for page in range(1, pages + 1):
            params = {
                "key": GAODE_API_KEY,
                "keywords": criteria["keywords"], # 确保传入的是单个关键词
                "location": criteria["location"],
                "types": criteria.get("types", "050000"),
                "city": criteria.get("city", ""),
                "citylimit": "true", # [优化] 增加citylimit参数，确保结果在指定城市内
                "offset": str(offset),
                "page": str(page),
                "extensions": "all"
            }
            
            print(f"  > 正在向高德API发送请求: {params}")
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "1":
                error_info = data.get("info", "未知的高德API业务错误")
                raise ValueError(f"高德API业务错误: {error_info}")

            raw_pois = data.get("pois", [])

            for poi in raw_pois:
                biz_ext = poi.get("biz_ext", {})
                all_results.append({
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "location": poi.get("location"),
                    "telephone": poi.get("tel"),
                    "type": poi.get("type"),
                    "rating": biz_ext.get("rating"),
                    "cost": biz_ext.get("cost"),
                })

            # 如果本页结果少于offset，说明没有更多数据
            if len(raw_pois) < offset:
                break
        
        print(f"  < 成功获取并清洗了 {len(all_results)} 条餐厅信息。")
        state['search_results'] = all_results

    except requests.exceptions.Timeout:
        error_msg = "网络错误：请求高德API超时。"
        state['error_messages'].append(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"网络错误：请求高德API失败。详情: {e}"
        state['error_messages'].append(error_msg)
    except ValueError as e:
        error_msg = f"数据错误: {e}"
        state['error_messages'].append(error_msg)
    except Exception as e:
        error_msg = f"未知错误: {e.__class__.__name__} - {e}"
        state['error_messages'].append(error_msg)
        
    return state

food_search_builder = StateGraph(FoodSearchState)
food_search_builder.add_node("gaode_search", gaode_poi_search_node)
food_search_builder.set_entry_point("gaode_search")
food_search_builder.add_edge("gaode_search", END)
food_search_agent = food_search_builder.compile()