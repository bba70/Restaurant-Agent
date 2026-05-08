import json
import os
from typing import List, Optional, TypedDict

import requests

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from config import ALIYUN_API_KEY, ALIYUN_BASE_URL, ALIYUN_MODEL, GAODE_API_KEY
from prompt.parse_query import (
    PARSE_QUERY_SYSTEM_PROMPT,
    PARSE_QUERY_USER_PROMPT_TEMPLATE,
)


DEFAULT_CITY = os.getenv("DEFAULT_CITY", "北京")
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "116.397128,39.916527")

CITY_LOCATION_MAP = {
    "北京": "116.397128,39.916527",
    "上海": "121.473701,31.230416",
    "广州": "113.264385,23.129112",
    "深圳": "114.057868,22.543099",
    "杭州": "120.15507,30.274085",
}


class ParseQueryState(TypedDict):
    """参数解析状态"""

    query: str
    city: Optional[str]
    confidence: Optional[float]
    reason: Optional[str]
    location_source: Optional[str]
    location_text: Optional[str]
    location: Optional[str]
    locations: List[dict]
    location_count: int
    error_messages: List[str]


def parse_query_node(state: ParseQueryState) -> ParseQueryState:
    """解析用户查询中的城市和多地点信息，缺失时回退到定位结果"""

    print("--- [Agent] 进入 参数解析Agent ---")

    query = state.get("query", "").strip()
    state.setdefault("error_messages", [])
    state.setdefault("locations", [])
    if not query:
        error_msg = "输入错误：query 不能为空。"
        print(f"  < {error_msg}")
        state["error_messages"].append(error_msg)
        state["city"] = None
        state["confidence"] = None
        state["reason"] = None
        state["location_source"] = None
        state["location_text"] = None
        state["location"] = None
        state["locations"] = []
        state["location_count"] = 0
        return state

    llm = ChatOpenAI(
        api_key=ALIYUN_API_KEY,
        base_url=ALIYUN_BASE_URL,
        model=ALIYUN_MODEL,
        temperature=0,
    )

    messages = [
        {"role": "system", "content": PARSE_QUERY_SYSTEM_PROMPT},
        {"role": "user", "content": PARSE_QUERY_USER_PROMPT_TEMPLATE.format(query=query)},
    ]

    try:
        print(f"  > 正在解析 query: {query}")
        response = llm.invoke(messages)
        response_text = response.content.strip()
        result = json.loads(response_text)

        city = result.get("city")
        raw_locations = result.get("locations", [])
        confidence = result.get("confidence")
        reason = result.get("reason")

        if not raw_locations:
            raw_locations = [{"name": city or "当前位置", "location_text": city or "当前位置"}]

        if city:
            print(f"  < 识别到城市: {city} (置信度: {confidence}), 地点数: {len(raw_locations)}")
            state["city"] = city
            state["confidence"] = confidence
            state["reason"] = reason or "来自用户 query 的明确城市"
            state["location_source"] = "query"
        else:
            detected_city, detected_location = _detect_current_city_and_location()
            if detected_city:
                print(f"  < 未识别城市，使用定位结果: {detected_city}")
                state["city"] = detected_city
                state["confidence"] = 1.0
                state["reason"] = "来自设备定位"
                state["location_source"] = "device"
            else:
                error_msg = "无法确定用户所在城市"
                print(f"  < {error_msg}")
                state["error_messages"].append(error_msg)
                state["city"] = None
                state["confidence"] = 0.0
                state["reason"] = reason or "未能识别城市"
                state["location_source"] = None
                state["locations"] = []
                state["location_count"] = 0
                state["location_text"] = None
                state["location"] = None
                return state

        resolved_city = state.get("city", "")

        # 对每个地点独立调用高德地理编码
        resolved_locations = []
        geocode_failures = 0
        for loc in raw_locations:
            name = loc.get("name", loc.get("location_text", ""))
            loc_text = loc.get("location_text", "")
            search_text = loc_text or name
            lnglat = _geocode_location(search_text, resolved_city)

            if lnglat:
                resolved_locations.append({"name": name, "lnglat": lnglat})
                print(f"  < 地点 '{name}': {lnglat}")
            else:
                resolved_locations.append({"name": name, "lnglat": None})
                geocode_failures += 1
                error_msg = f"地点 '{name}' 地理编码失败"
                state["error_messages"].append(error_msg)
                print(f"  < {error_msg}")

        state["locations"] = resolved_locations
        state["location_count"] = len(resolved_locations)

        # 向后兼容：设置 location 和 location_text 为第一个有效地点
        if resolved_locations:
            first_valid = next((loc for loc in resolved_locations if loc["lnglat"]), resolved_locations[0])
            state["location"] = first_valid.get("lnglat")
            state["location_text"] = first_valid.get("name")
            # 如果第一个地点 geocode 失败，尝试 fallback
            if state["location"] is None:
                fallback_lnglat = _fallback_location(resolved_city)
                state["location"] = fallback_lnglat
        else:
            fallback_lnglat = _fallback_location(resolved_city)
            state["location"] = fallback_lnglat
            state["location_text"] = resolved_city

    except json.JSONDecodeError as exc:
        error_msg = f"JSON解析失败: {exc}"
        print(f"  < {error_msg}")
        state.setdefault("error_messages", []).append(error_msg)
    except Exception as exc:
        error_msg = f"参数解析失败: {exc}"
        print(f"  < {error_msg}")
        state["error_messages"].append(error_msg)

    return state


def _geocode_location(location_text: Optional[str], city: Optional[str]) -> Optional[str]:
    if not location_text:
        return None
    if not GAODE_API_KEY:
        return None
    params = {
        "key": GAODE_API_KEY,
        "address": location_text,
    }
    if city:
        params["city"] = city
    try:
        response = requests.get("https://restapi.amap.com/v3/geocode/geo", params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "1":
            info = data.get("info", "未知地理编码错误")
            print(f"  < 地理编码失败: {info}")
            return None
        geocodes = data.get("geocodes", [])
        if not geocodes:
            return None
        return geocodes[0].get("location")
    except requests.RequestException as exc:
        print(f"  < 地理编码请求失败: {exc}")
        return None


def _fallback_location(city: Optional[str]) -> Optional[str]:
    if city and city in CITY_LOCATION_MAP:
        return CITY_LOCATION_MAP[city]
    return DEFAULT_LOCATION


def _detect_current_city_and_location() -> (Optional[str], Optional[str]):
    city = os.getenv("DEFAULT_CITY") or DEFAULT_CITY
    location = os.getenv("DEFAULT_LOCATION")
    if not location:
        location = CITY_LOCATION_MAP.get(city)
    if not location:
        location = DEFAULT_LOCATION
    return city, location


parse_query_builder = StateGraph(ParseQueryState)
parse_query_builder.add_node("parse_query", parse_query_node)
parse_query_builder.set_entry_point("parse_query")
parse_query_builder.add_edge("parse_query", END)
parse_query_agent = parse_query_builder.compile()
