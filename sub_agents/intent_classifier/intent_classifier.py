import json
from typing import List, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from config import ALIYUN_API_KEY, ALIYUN_BASE_URL, ALIYUN_MODEL
from prompt.intent_classifier import (
    INTENT_CLASSIFIER_SYSTEM_PROMPT,
    INTENT_CLASSIFIER_USER_PROMPT_TEMPLATE,
)

INTENT_MODE_MAP = {
    "single_location": "single",
    "equidistant_meeting": "intersection",
    "along_route": "along_route",
    "compare_locations": "union",
}


class IntentClassifierState(TypedDict):
    query: str
    location_count: int
    intent: Optional[str]
    search_mode: Optional[str]
    confidence: Optional[float]
    error_messages: List[str]


def intent_classifier_node(state: IntentClassifierState) -> IntentClassifierState:
    """根据用户 query 和地点数量识别搜索意图并输出 search_mode"""

    print("--- [Agent] 进入 意图分类Agent ---")

    query = state.get("query", "").strip()
    location_count = state.get("location_count", 1)
    state.setdefault("error_messages", [])

    if not query:
        state["intent"] = "single_location"
        state["search_mode"] = "single"
        state["confidence"] = 0.0
        state["error_messages"].append("输入错误：query 为空，默认 single")
        return state

    llm = ChatOpenAI(
        api_key=ALIYUN_API_KEY,
        base_url=ALIYUN_BASE_URL,
        model=ALIYUN_MODEL,
        temperature=0,
    )

    messages = [
        {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": INTENT_CLASSIFIER_USER_PROMPT_TEMPLATE.format(
            query=query,
            location_count=location_count,
        )},
    ]

    try:
        print(f"  > 正在分类意图: query={query[:50]}..., location_count={location_count}")
        response = llm.invoke(messages)
        response_text = response.content.strip()
        result = json.loads(response_text)

        intent = result.get("intent", "single_location")
        search_mode = result.get("search_mode") or INTENT_MODE_MAP.get(intent, "single")
        confidence = result.get("confidence", 0.5)

        # 低置信度回退
        if confidence < 0.5:
            state["error_messages"].append(
                f"意图分类置信度低 ({confidence})，回退为 single 模式"
            )
            search_mode = "single"
            intent = "single_location"

        state["intent"] = intent
        state["search_mode"] = search_mode
        state["confidence"] = confidence
        print(f"  < 意图: {intent}, search_mode: {search_mode}, 置信度: {confidence}")

    except json.JSONDecodeError as exc:
        error_msg = f"意图分类JSON解析失败: {exc}"
        print(f"  < {error_msg}")
        state["error_messages"].append(error_msg)
        state["intent"] = "single_location"
        state["search_mode"] = "single"
        state["confidence"] = 0.0
    except Exception as exc:
        error_msg = f"意图分类失败: {exc}"
        print(f"  < {error_msg}")
        state["error_messages"].append(error_msg)
        state["intent"] = "single_location"
        state["search_mode"] = "single"
        state["confidence"] = 0.0

    return state


intent_classifier_builder = StateGraph(IntentClassifierState)
intent_classifier_builder.add_node("classify", intent_classifier_node)
intent_classifier_builder.set_entry_point("classify")
intent_classifier_builder.add_edge("classify", END)
intent_classifier_agent = intent_classifier_builder.compile()
