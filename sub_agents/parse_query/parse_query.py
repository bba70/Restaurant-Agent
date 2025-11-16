import json
import os
from typing import List, Optional, TypedDict

import requests

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from config import ALIYUN_API_KEY, ALIYUN_BASE_URL, ALIYUN_MODEL, GAODE_API_KEY, DEFAULT_CITY, DEFAULT_LOCATION
from prompt.parse_query import (
    PARSE_QUERY_SYSTEM_PROMPT,
    PARSE_QUERY_USER_PROMPT_TEMPLATE,
)

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
    error_messages: List[str]


def parse_query_node(state: ParseQueryState) -> ParseQueryState:
    """解析用户查询中的城市信息，缺失时回退到定位结果"""

    print("--- [Agent] 进入 参数解析Agent ---")

    query = state.get("query", "").strip()
    state.setdefault("error_messages", [])
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
        location_text = result.get("location_text") or city
        confidence = result.get("confidence")
        reason = result.get("reason")

        if city:
            print(f"  < 识别到城市: {city} (置信度: {confidence})")
            state["city"] = city
            state["confidence"] = confidence
            state["reason"] = reason or "来自用户 query 的明确城市"
            state["location_source"] = "query"
            state["location_text"] = location_text
            best_location = _geocode_location(location_text, city)
            if not best_location:
                best_location = _fallback_location(city)
            state["location"] = best_location
        else:
            detected_city, detected_location = _detect_current_city_and_location()
            if detected_city:
                print(f"  < 未识别城市，使用定位结果: {detected_city}")
                state["city"] = detected_city
                state["confidence"] = 1.0
                state["reason"] = "来自设备定位"
                state["location_source"] = "device"
                state["location_text"] = detected_city
                state["location"] = detected_location
            else:
                error_msg = "无法确定用户所在城市"
                print(f"  < {error_msg}")
                state["error_messages"].append(error_msg)
                state["city"] = None
                state["confidence"] = 0.0
                state["reason"] = reason or "未能识别城市"
                state["location_source"] = None
                state["location_text"] = None
                state["location"] = None

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
