import math
import os
import time
import requests
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from config import GAODE_API_KEY


# 高德 API 调用频率限制（秒）
_GAODE_API_CALL_INTERVAL = 1.0
_last_gaode_api_call_time = 0.0


class FoodSearchState(TypedDict):
    search_criteria: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    locations: List[dict]
    search_mode: str
    fallback: Optional[str]
    error_messages: List[str]


def haversine_distance(lnglat1: str, lnglat2: str) -> float:
    """计算两个经纬度坐标之间的 Haversine 距离（单位：米）"""
    lng1, lat1 = map(float, lnglat1.split(","))
    lng2, lat2 = map(float, lnglat2.split(","))
    R = 6371000  # 地球半径（米）
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _fetch_pois_from_gaode(keywords: str, location: str, types: str, city: str,
                           radius: Optional[int] = None, offset: int = 20, pages: int = 5) -> List[Dict[str, Any]]:
    """从高德 API 获取 POI 列表的通用函数"""
    global _last_gaode_api_call_time

    api_url = "https://restapi.amap.com/v3/place/around"
    all_results: List[Dict[str, Any]] = []

    for page in range(1, pages + 1):
        # 频率限制：确保每次调用间隔至少 _GAODE_API_CALL_INTERVAL 秒
        current_time = time.time()
        elapsed = current_time - _last_gaode_api_call_time
        if elapsed < _GAODE_API_CALL_INTERVAL:
            sleep_time = _GAODE_API_CALL_INTERVAL - elapsed
            time.sleep(sleep_time)

        params = {
            "key": GAODE_API_KEY,
            "keywords": keywords,
            "location": location,
            "types": types,
            "city": city or "",
            "citylimit": "true",
            "offset": str(offset),
            "page": str(page),
            "extensions": "all",
        }
        if radius is not None:
            params["radius"] = str(radius)

        try:
            response = requests.get(api_url, params=params, timeout=10)
            _last_gaode_api_call_time = time.time()
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

            if len(raw_pois) < offset:
                break
        except Exception:
            raise
        finally:
            # 每次调用后固定 sleep 0.5 秒
            time.sleep(0.5)

    return all_results


def _match_poi(poi_a: Dict[str, Any], poi_b: Dict[str, Any]) -> bool:
    """判断两个 POI 是否为同一家餐厅：名称包含/编辑距离 + 坐标 < 100m"""
    name_a = poi_a.get("name", "")
    name_b = poi_b.get("name", "")
    loc_a = poi_a.get("location", "")
    loc_b = poi_b.get("location", "")

    if not name_a or not name_b or not loc_a or not loc_b:
        return False

    # 名称匹配：包含关系
    name_match = (name_a in name_b or name_b in name_a)
    if not name_match:
        # 编辑距离 < 3
        edit_dist = _edit_distance(name_a, name_b)
        name_match = edit_dist < 3

    # 坐标匹配：Haversine < 100m
    coord_match = haversine_distance(loc_a, loc_b) < 100

    return name_match and coord_match


def _edit_distance(s1: str, s2: str) -> int:
    """Levenshtein 编辑距离"""
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insert = prev_row[j + 1] + 1
            delete = curr_row[j] + 1
            replace = prev_row[j] + (c1 != c2)
            curr_row.append(min(insert, delete, replace))
        prev_row = curr_row
    return prev_row[-1]


def _search_single(step_input: dict) -> List[Dict[str, Any]]:
    """单点搜索：封装现有逻辑，以 location 为中心搜索"""
    keywords = step_input.get("keywords") or "美食"
    location = step_input.get("location")
    types = step_input.get("types") or "050000"
    city = step_input.get("city", "")

    location_keywords = ["附近", "周边", "旁边", "靠近", "距离", "方圆"]
    if any(kw in keywords for kw in location_keywords):
        print(f"  > 检测到位置词汇，使用默认关键词'美食'代替'{keywords}'")
        keywords = "美食"

    return _fetch_pois_from_gaode(keywords, location, types, city)


def _search_intersection(step_input: dict, locations: List[dict]) -> List[Dict[str, Any]]:
    """多点搜索：分别搜索 → POI 模糊匹配 → 严格交集"""
    keywords = step_input.get("keywords") or "美食"
    types = step_input.get("types") or "050000"
    city = step_input.get("city", "")

    # 1. 各地点独立搜索
    all_poi_sets = []
    for loc in locations:
        lnglat = loc.get("lnglat")
        if not lnglat:
            print(f"  ! 地点 '{loc.get('name')}' 无有效经纬度，跳过")
            continue
        print(f"  > 搜索地点 '{loc.get('name')}' ({lnglat})")
        pois = _fetch_pois_from_gaode(keywords, lnglat, types, city)
        all_poi_sets.append(pois)
        print(f"    结果数: {len(pois)}")

    if not all_poi_sets:
        return []

    # 2. 严格交集
    intersection = list(all_poi_sets[0])
    for poi_set in all_poi_sets[1:]:
        matched = []
        for p in intersection:
            if any(_match_poi(p, candidate) for candidate in poi_set):
                matched.append(p)
        intersection = matched

    print(f"  < 严格交集中: {len(intersection)} 家餐厅")
    return intersection


def _fallback_midpoint_search(step_input: dict, locations: List[dict]) -> List[Dict[str, Any]]:
    """降级策略：计算几何中点 → 扩大半径搜索"""
    keywords = step_input.get("keywords") or "美食"
    types = step_input.get("types") or "050000"
    city = step_input.get("city", "")

    valid_locations = [loc for loc in locations if loc.get("lnglat")]
    if not valid_locations:
        return []

    # 计算几何中点
    lngs = []
    lats = []
    for loc in valid_locations:
        lng, lat = loc["lnglat"].split(",")
        lngs.append(float(lng))
        lats.append(float(lat))
    mid_lng = sum(lngs) / len(lngs)
    mid_lat = sum(lats) / len(lats)
    midpoint = f"{mid_lng:.6f},{mid_lat:.6f}"

    # 计算最大地点间距离
    max_dist = 0
    for i in range(len(valid_locations)):
        for j in range(i + 1, len(valid_locations)):
            d = haversine_distance(valid_locations[i]["lnglat"], valid_locations[j]["lnglat"])
            if d > max_dist:
                max_dist = d

    radius = int(max_dist / 2 + 2000)
    print(f"  > 降级：中点 {midpoint}，半径 {radius}m")

    results = _fetch_pois_from_gaode(keywords, midpoint, types, city, radius=radius)
    for r in results:
        r["_fallback"] = True
    return results


def gaode_poi_search_node(state: FoodSearchState) -> FoodSearchState:
    """高德地图POI搜索节点，根据 search_mode 路由到不同搜索分支"""

    print("--- [Agent] 进入 高德美食搜索Agent ---")

    if not GAODE_API_KEY:
        raise EnvironmentError("错误：GAODE_API_KEY 未设置。")

    criteria = state.get("search_criteria") or {}
    search_mode = state.get("search_mode") or criteria.get("search_mode", "single")
    locations = state.get("locations") or criteria.get("locations", [])
    state.setdefault("error_messages", [])
    state.setdefault("fallback", None)

    # 构建统一的搜索输入
    step_input = {
        "keywords": criteria.get("keywords") or "美食",
        "location": criteria.get("location"),
        "types": criteria.get("types") or "050000",
        "city": criteria.get("city", ""),
    }

    try:
        if search_mode == "single":
            print(f"  > 单点搜索模式")
            results = _search_single(step_input)

        elif search_mode == "intersection":
            print(f"  > 多点等距搜索模式，地点数: {len(locations)}")
            results = _search_intersection(step_input, locations)

            if not results and len(locations) >= 2:
                print(f"  > 严格交集为空，触发降级中点搜索")
                results = _fallback_midpoint_search(step_input, locations)
                state["fallback"] = "midpoint"

        elif search_mode in ("along_route", "union"):
            error_msg = f"search_mode '{search_mode}' 尚未实现"
            print(f"  < {error_msg}")
            state["error_messages"].append(error_msg)
            state["search_results"] = []
            return state

        else:
            error_msg = f"未知的 search_mode: {search_mode}"
            state["error_messages"].append(error_msg)
            state["search_results"] = []
            return state

        # 为每个结果计算到各参考点的距离
        valid_locations = [loc for loc in locations if loc.get("lnglat")]
        for poi in results:
            distances = []
            for loc in valid_locations:
                try:
                    d = haversine_distance(poi["location"], loc["lnglat"])
                    distances.append(round(d, 1))
                except (ValueError, KeyError):
                    distances.append(-1)
            poi["distances"] = distances

        print(f"  < 成功获取 {len(results)} 条餐厅信息")
        state["search_results"] = results

    except requests.exceptions.Timeout:
        error_msg = "网络错误：请求高德API超时。"
        state["error_messages"].append(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"网络错误：请求高德API失败。详情: {e}"
        state["error_messages"].append(error_msg)
    except ValueError as e:
        error_msg = f"数据错误: {e}"
        state["error_messages"].append(error_msg)
    except Exception as e:
        error_msg = f"未知错误: {e.__class__.__name__} - {e}"
        state["error_messages"].append(error_msg)

    return state


food_search_builder = StateGraph(FoodSearchState)
food_search_builder.add_node("gaode_search", gaode_poi_search_node)
food_search_builder.set_entry_point("gaode_search")
food_search_builder.add_edge("gaode_search", END)
food_search_agent = food_search_builder.compile()
