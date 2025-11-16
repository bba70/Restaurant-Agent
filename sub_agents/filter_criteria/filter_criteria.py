"""
条件筛选 Agent - 从用户查询中提取筛选条件
"""
import json
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from config import ALIYUN_API_KEY, ALIYUN_BASE_URL, ALIYUN_MODEL
from prompt.filter_criteria import (
    FILTER_CRITERIA_SYSTEM_PROMPT,
    FILTER_CRITERIA_USER_PROMPT_TEMPLATE,
)


class FilterCriteriaState(TypedDict):
    """筛选条件状态"""
    query: str  # 用户原始查询
    filters: Optional[Dict[str, Any]]  # 提取的筛选条件
    confidence: Optional[float]  # 置信度（0-1）
    error_messages: List[str]  # 错误信息


def filter_criteria_node(state: FilterCriteriaState) -> FilterCriteriaState:
    """
    条件筛选节点：从用户查询中提取筛选条件
    
    职责:
        1. 从用户查询中识别价格、评分、距离等条件
        2. 返回结构化的筛选参数
        3. 返回置信度
    
    输入:
        state: FilterCriteriaState
            - query: 用户原始查询
    
    输出:
        state: FilterCriteriaState
            - filters: 提取的筛选条件字典
            - confidence: 置信度
            - error_messages: 错误信息（如果有）
    """
    
    print("--- [Agent] 进入 条件筛选Agent ---")
    
    query = state.get("query", "")
    if not query:
        error_msg = "输入错误：query 不能为空。"
        print(f"  < {error_msg}")
        state['error_messages'].append(error_msg)
        return state
    
    # 初始化LLM
    llm = ChatOpenAI(
        api_key=ALIYUN_API_KEY,
        base_url=ALIYUN_BASE_URL,
        model=ALIYUN_MODEL,
        temperature=0
    )
    
    # 构建提示词
    system_prompt = FILTER_CRITERIA_SYSTEM_PROMPT
    user_prompt = FILTER_CRITERIA_USER_PROMPT_TEMPLATE.format(query=query)
    
    try:
        print(f"  > 正在分析查询中的筛选条件: {query}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # 解析JSON响应
        result = json.loads(response_text)
        
        filters = result.get("filters")
        confidence = result.get("confidence", 0.0)
        
        if filters:
            print(f"  < 识别到筛选条件: {filters} (置信度: {confidence})")
            state['filters'] = filters
            state['confidence'] = confidence
        else:
            print(f"  < 未识别到明确的筛选条件")
            state['filters'] = {}
            state['confidence'] = 0.0
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON解析失败: {e}"
        print(f"  < {error_msg}")
        state['error_messages'].append(error_msg)
    except Exception as e:
        error_msg = f"条件筛选失败: {e}"
        print(f"  < {error_msg}")
        state['error_messages'].append(error_msg)
    
    return state


# 构建条件筛选Agent
filter_criteria_builder = StateGraph(FilterCriteriaState)
filter_criteria_builder.add_node("filter", filter_criteria_node)
filter_criteria_builder.set_entry_point("filter")
filter_criteria_builder.add_edge("filter", END)
filter_criteria_agent = filter_criteria_builder.compile()
