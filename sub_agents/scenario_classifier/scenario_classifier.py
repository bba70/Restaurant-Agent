import os
import json
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from config import ALIYUN_API_KEY, ALIYUN_BASE_URL, ALIYUN_MODEL
from prompt.scenario_classifier import (
    SCENARIO_CLASSIFIER_SYSTEM_PROMPT,
    SCENARIO_CLASSIFIER_USER_PROMPT_TEMPLATE,
)


# 加载高德POI映射表
def _load_taxonomy_map() -> Dict[str, Dict[str, Any]]:
    """
    加载高德POI映射表
    
    返回:
        映射表字典，格式为 {key: {"medium_category": str, "small_category": str, "type": str}}
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    taxonomy_file = os.path.join(current_dir, "restaurant_taxonomy.json")
    
    if not os.path.exists(taxonomy_file):
        print(f"警告：未找到映射表文件 {taxonomy_file}，将使用空映射表")
        return {}
    
    try:
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            taxonomy_map = json.load(f)
        print(f"✓ 成功加载映射表，共 {len(taxonomy_map)} 个映射关系")
        return taxonomy_map
    except Exception as e:
        print(f"警告：加载映射表失败 {e}，将使用空映射表")
        return {}


# 全局映射表
TAXONOMY_MAP = _load_taxonomy_map()


class ScenarioClassifierState(TypedDict):
    """情景分类状态"""
    query: str  # 用户原始查询
    scenario: Optional[str]  # 识别到的场景
    types: Optional[str]  # 映射后的高德API餐厅类型（type参数）
    confidence: Optional[float]  # 置信度（0-1）
    error_messages: List[str]  # 错误信息


def scenario_classifier_node(state: ScenarioClassifierState) -> ScenarioClassifierState:
    """
    情景分类节点：使用LLM识别用户查询中的场景信息
    
    职责:
        1. 从用户查询中识别场景（如：聚餐、约会、商务等）
        2. 根据场景映射到对应的高德API餐厅类型（type参数）
        3. 返回识别的场景、类型和置信度
    
    输入:
        state: ScenarioClassifierState
            - query: 用户原始查询
    
    输出:
        state: ScenarioClassifierState
            - scenario: 识别到的场景
            - restaurant_type: 映射后的高德API type值
            - confidence: 置信度
            - error_messages: 错误信息（如果有）
    """
    
    print("--- [Agent] 进入 情景分类Agent ---")
    
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
    system_prompt = SCENARIO_CLASSIFIER_SYSTEM_PROMPT
    user_prompt = SCENARIO_CLASSIFIER_USER_PROMPT_TEMPLATE.format(query=query)
    
    try:
        print(f"  > 正在分析查询: {query}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # 解析JSON响应
        result = json.loads(response_text)
        
        scenario = result.get("scenario")
        confidence = result.get("confidence", 0.0)
        
        if scenario:
            print(f"  < 识别到场景: {scenario} (置信度: {confidence})")
            state['scenario'] = scenario
            state['confidence'] = confidence
            
            # 从映射表中查询对应的 type
            amap_type = _get_restaurant_type_from_scenario(scenario)
            if amap_type:
                print(f"  < 映射到高德API type: {amap_type}")
                state['types'] = amap_type
            else:
                print(f"  < 未在映射表中找到对应的type")
                state['types'] = None
        else:
            print(f"  < 未识别到明确的场景")
            state['scenario'] = None
            state['confidence'] = 0.0
            state['types'] = None
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON解析失败: {e}"
        print(f"  < {error_msg}")
        state['error_messages'].append(error_msg)
    except Exception as e:
        error_msg = f"情景分类失败: {e}"
        print(f"  < {error_msg}")
        state['error_messages'].append(error_msg)
    
    return state


def _get_restaurant_type_from_scenario(scenario: str) -> Optional[str]:
    """
    根据识别的场景从映射表中查询对应的高德API type
    
    参数:
        scenario: 识别到的场景或餐厅类型名称
    
    返回:
        高德API的type值，如果未找到则返回None
    """
    if not scenario or not TAXONOMY_MAP:
        return None
    
    scenario = scenario.strip()
    
    # 方式1：精确匹配（中类-小类 格式）
    if scenario in TAXONOMY_MAP:
        return TAXONOMY_MAP[scenario].get("type")
    
    # 方式2：精确匹配中类或小类
    for key, value in TAXONOMY_MAP.items():
        medium = value.get("medium_category", "")
        small = value.get("small_category", "")
        
        if scenario == medium or scenario == small:
            return value.get("type")
    
    # 方式3：模糊匹配（包含关系）- 处理部分匹配的情况
    for key, value in TAXONOMY_MAP.items():
        medium = value.get("medium_category", "")
        small = value.get("small_category", "")
        
        # 如果scenario包含在中类或小类中，或反过来
        if scenario in medium or scenario in small or medium in scenario or small in scenario:
            return value.get("type")
    
    return None


# 构建情景分类Agent
scenario_classifier_builder = StateGraph(ScenarioClassifierState)
scenario_classifier_builder.add_node("classifier", scenario_classifier_node)
scenario_classifier_builder.set_entry_point("classifier")
scenario_classifier_builder.add_edge("classifier", END)
scenario_classifier_agent = scenario_classifier_builder.compile()
