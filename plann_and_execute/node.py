import json
import re
from typing import Optional, List, Callable, Dict, Any
from langchain_openai import ChatOpenAI
from config import ALIYUN_API_KEY, ALIYUN_BASE_URL, ALIYUN_MODEL
from plann_and_execute.state import OrchestratorState, Plan, PlanStep
from prompt.planner import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT_TEMPLATE,
    PLANNER_REPLAN_PROMPT_TEMPLATE,
)
from sub_agents.scenario_classifier import scenario_classifier_agent
from sub_agents.parse_query.parse_query import parse_query_agent
from sub_agents.food_search.food_search import food_search_agent


def planner_node(state: OrchestratorState) -> OrchestratorState:
    '''
    计划节点：根据用户查询生成执行计划
    
    输入:
        state: OrchestratorState
            - query: 用户查询
            - replan_count: 重试次数（0表示初始规划）
            - error_info: 前一次执行的错误信息（重规划时使用）
            - past_plans: 之前失败的计划列表
    
    输出:
        state: OrchestratorState
            - plan: Plan 对象，包含 List[PlanStep]
            - current_step: 初始化为1
            - step_results: 初始化为空字典
            - past_plans: 更新后的计划历史（重规划时）
    '''
    
    # 初始化LLM
    llm = ChatOpenAI(
        api_key=ALIYUN_API_KEY,
        base_url=ALIYUN_BASE_URL,
        model=ALIYUN_MODEL,
        temperature=0
    )
    
    # 判断是否是重规划
    is_replan = state.get("replan_count", 0) > 0
    
    available_subgraphs_text = _format_subgraph_catalog()

    # 构建提示词
    strict_instruction = "\n重要要求: 仅能使用上述列表中的子图, 并且 `subgraph_name` 必须与列表中的键完全一致, 不得新增或改名。"

    if is_replan:
        # 重规划模式
        error_info = json.dumps(state.get("error_info", {}), ensure_ascii=False, indent=2)
        past_plans = "\n".join(state.get("past_plans", []))
        user_prompt = PLANNER_REPLAN_PROMPT_TEMPLATE.format(
            query=state["query"],
            error_info=error_info,
            past_plans=past_plans,
            replan_count=state.get("replan_count", 0)
        ) + f"\n\n可用子图列表:\n{available_subgraphs_text}{strict_instruction}"
    else:
        # 初始规划模式
        past_plans = "\n".join(state.get("past_plans", []))
        user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
            query=state["query"],
            past_plans=past_plans if past_plans else "无",
            replan_count=state.get("replan_count", 0)
        ) + f"\n\n可用子图列表:\n{available_subgraphs_text}{strict_instruction}"
    
    # 调用LLM
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    response = llm.invoke(messages)
    response_text = response.content.strip()
    
    # 解析JSON响应
    plan_dict = _parse_plan_response(response_text)
    
    # 构建规范的 PlanStep 列表
    plan_steps: List[PlanStep] = [
        PlanStep(
            step_id=step["step_id"],
            subgraph_name=step["subgraph_name"],
            description=step["description"],
            input_mapping=step.get("input_mapping")
        )
        for step in plan_dict["steps"]
    ]
    
    # 构建 Plan 对象（规范的计划结构）
    plan: Plan = Plan(steps=plan_steps)
    
    # 更新state
    state["plan"] = plan
    state["current_step"] = 0
    state["step_results"] = {}
    
    # 如果是重规划，记录新的计划
    if is_replan:
        past_plans_list = state.get("past_plans", [])
        past_plans_list.append(json.dumps(plan_dict, ensure_ascii=False))
        state["past_plans"] = past_plans_list
    
    print(f"--- 规划完成 ---")
    print(f"计划步骤数: {len(plan_steps)}")
    for step in plan_steps:
        print(f"  Step {step.step_id}: {step.subgraph_name} - {step.description}")
    
    return state


def _parse_plan_response(response_text: str) -> dict:
    """
    解析LLM的JSON响应
    处理可能的markdown代码块包装
    """
    # 移除markdown代码块标记
    response_text = re.sub(r'^```json\s*', '', response_text)
    response_text = re.sub(r'^```\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text)
    response_text = response_text.strip()
    
    try:
        plan_dict = json.loads(response_text)
        return plan_dict
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"响应内容: {response_text}")
        raise ValueError(f"无法解析LLM的计划响应: {e}")


def executor_node(state: OrchestratorState) -> OrchestratorState:
    '''
    执行器节点：递增当前步骤计数
    
    职责:
        1. 递增 current_step 指向下一步
    
    输入:
        state: OrchestratorState
            - current_step: 当前步骤序号
    
    输出:
        state: OrchestratorState
            - current_step: 递增后的步骤序号
    '''
    
    current_step_index: int = state["current_step"]
    
    print(f"\n--- 执行器递增步骤 ---")
    print(f"当前步骤: {current_step_index}")
    
    # 更新current_step指向下一步
    state["current_step"] = current_step_index + 1
    
    print(f"下一步骤: {state['current_step']}")
    
    return state


def subgraph_node(state: OrchestratorState) -> OrchestratorState:
    '''
    子图执行节点：根据current_step从plan中获取步骤并执行
    
    职责:
        1. 读取 current_step
        2. 从 plan 中获取对应的 PlanStep
        3. 根据 input_mapping 准备输入参数
        4. 调用对应的子图执行
        5. 将执行结果存储到 step_results
    
    输入:
        state: OrchestratorState
            - plan: 完整的计划（Plan对象）
            - current_step: 当前步骤序号
            - step_results: 之前步骤的执行结果
            - query: 用户原始查询
    
    输出:
        state: OrchestratorState
            - step_results: 添加当前步骤的执行结果
            - error_info: 执行过程中的错误信息（如果有）
    '''
    
    plan: Plan = state["plan"]
    current_step_index: int = state["current_step"]
    step_results: dict = state.get("step_results", {})
    original_query: str = state.get("query", "")
    
    # 检查当前步骤是否超出计划范围
    if current_step_index > len(plan.steps):
        print(f"\n--- 子图执行 ---")
        print(f"错误: 步骤 {current_step_index} 超出计划范围（总共 {len(plan.steps)} 步）")
        state["error_info"] = {
            "error_type": "OUT_OF_RANGE",
            "message": f"步骤 {current_step_index} 超出计划范围",
            "step": current_step_index
        }
        return state
    
    # 从plan中获取当前步骤（current_step是1-indexed）
    current_plan_step: PlanStep = plan.steps[current_step_index - 1]
    
    print(f"\n--- 子图执行 ---")
    print(f"当前步骤: {current_step_index}/{len(plan.steps)}")
    print(f"子图名称: {current_plan_step.subgraph_name}")
    print(f"步骤描述: {current_plan_step.description}")
    
    # 准备该步骤的输入参数
    step_input: dict = _prepare_step_input(
        current_plan_step,
        step_results,
        original_query
    )
    
    print(f"步骤输入: {step_input}")
    
    # 调用子图执行
    try:
        step_result: dict = _execute_subgraph(
            current_plan_step.subgraph_name,
            step_input
        )
        
        print(f"步骤结果: {step_result}")
        
        # 将结果存储到step_results
        step_results[current_plan_step.step_id] = step_result
        state["step_results"] = step_results
        state["error_info"] = None
            
    except Exception as e:
        print(f"错误: 子图执行失败: {e}")
        state["error_info"] = {
            "error_type": "EXECUTION_ERROR",
            "message": str(e),
            "step": current_plan_step.step_id,
            "subgraph_name": current_plan_step.subgraph_name
        }

    return state


def _execute_subgraph(subgraph_name: str, step_input: dict) -> dict:
    executor = _SUBGRAPH_EXECUTORS.get(subgraph_name)
    if executor is None:
        raise ValueError(f"未注册的子图: {subgraph_name}")
    return executor(step_input)


def _run_scenario_classifier(step_input: dict) -> dict:
    scenario_state = {
        "query": step_input.get("query", ""),
        "scenario": None,
        "types": None,
        "confidence": None,
        "error_messages": [],
    }
    result = scenario_classifier_agent.invoke(scenario_state)
    return {
        "scenario": result.get("scenario"),
        "types": result.get("types"),
        "error_messages": result.get("error_messages", []),
    }


def _run_parse_query(step_input: dict) -> dict:
    parse_state = {
        "query": step_input.get("query", ""),
        "city": None,
        "confidence": None,
        "reason": None,
        "location_source": None,
        "location_text": None,
        "location": None,
        "error_messages": [],
    }
    result = parse_query_agent.invoke(parse_state)
    return {
        "city": result.get("city"),
        "location": result.get("location"),
        "error_messages": result.get("error_messages", []),
    }


def _run_food_search(step_input: dict) -> dict:
    keywords = step_input.get("keywords") or step_input.get("query")
    location = step_input.get("location") or step_input.get("city")
    types = step_input.get("types") or "050000"

    search_criteria = {
        "keywords": keywords,
        "location": location,
        "city": step_input.get("city"),
        "types": types,
    }

    food_state = {
        "search_criteria": search_criteria,
        "search_results": [],
        "error_messages": [],
    }

    result = food_search_agent.invoke(food_state)
    return {
        "search_results": result.get("search_results", []),
        "error_messages": result.get("error_messages", []),
    }


_SUBGRAPH_EXECUTORS: Dict[str, Callable[[Dict[str, Any]], dict]] = {
    "scenario_classifier": _run_scenario_classifier,
    "parse_query": _run_parse_query,
    "food_search": _run_food_search,
}

_SUBGRAPH_CATALOG: Dict[str, str] = {
    "scenario_classifier": "根据用户query识别就餐场景并映射高德API type",
    "parse_query": "解析用户query中的城市，缺失时回退到定位",
    "food_search": "调用高德美食搜索接口，返回清洗后的餐厅列表",
}


def _format_subgraph_catalog() -> str:
    lines = []
    for name, desc in _SUBGRAPH_CATALOG.items():
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def _prepare_step_input(
    step: PlanStep,
    step_results: dict,
    query: str
) -> dict:
    """
    根据input_mapping从step_results中提取输入
    
    参数:
        step: 当前计划步骤
        step_results: 之前步骤的执行结果 {step_id: result}
        query: 用户原始查询
    
    返回:
        该步骤的输入参数字典
    """
    step_input: dict = {}
    
    # 如果没有input_mapping，则使用原始query作为输入
    if step.input_mapping is None:
        step_input["query"] = query
        return step_input

    print("调试************")
    print(step_results)
    print("调试结束************")
    
    # 根据input_mapping提取输入
    for param_name, source_path in step.input_mapping.items():
        print("调试************")
        print(param_name)
        print(source_path)
        print("调试结束************")
        # 解析source_path: "step_X.field_name"
        if source_path.startswith("step_"):
            parts = source_path.split(".")
            if len(parts) == 2:
                step_id_str = parts[0].replace("step_", "")
                field_name = parts[1]
                
                try:
                    source_step_id = int(step_id_str)
                    
                    # 从step_results中获取该步骤的结果
                    if source_step_id in step_results:
                        source_result = step_results[source_step_id]
                        
                        # 如果结果是字典，提取指定字段
                        if isinstance(source_result, dict):
                            if field_name in source_result:
                                step_input[param_name] = source_result[field_name]
                            else:
                                print(f"警告: 步骤{source_step_id}的结果中找不到字段'{field_name}'")
                        else:
                            # 如果结果不是字典，直接使用
                            step_input[param_name] = source_result
                    else:
                        print(f"警告: 步骤{source_step_id}的结果不存在")
                
                except ValueError:
                    print(f"警告: 无法解析步骤ID '{step_id_str}'")
        else:
            # 如果source_path不是step_X格式，直接作为值使用
            step_input[param_name] = source_path
    
    # 如果仍未包含query，则回退到原始查询
    if "query" not in step_input:
        step_input["query"] = query
    
    return step_input

def formatter_node(state: OrchestratorState) -> OrchestratorState:
    '''格式化节点'''
    query = state.get("query", "")
    step_results = state.get("step_results", {}) or {}

    scenario_info = _extract_result(step_results, {"scenario", "types"})
    city_info = _extract_result(step_results, {"city", "location"})
    food_info = _extract_result(step_results, {"search_results"})

    restaurants = food_info.get("search_results", []) if isinstance(food_info, dict) else []
    errors: List[str] = []

    for result in step_results.values():
        if isinstance(result, dict) and result.get("error_messages"):
            errors.extend(result.get("error_messages", []))

    final_payload: Dict[str, Any] = {
        "query": query,
        "scenario": scenario_info.get("scenario") if isinstance(scenario_info, dict) else None,
        "types": scenario_info.get("types") if isinstance(scenario_info, dict) else None,
        "city": city_info.get("city") if isinstance(city_info, dict) else None,
        "location": city_info.get("location") if isinstance(city_info, dict) else None,
        "restaurant_count": len(restaurants),
        "restaurants": restaurants,
        "errors": errors,
    }

    state["final_result"] = json.dumps(final_payload, ensure_ascii=False, indent=2)
    print("\n--- 格式化输出 ---")
    print(state["final_result"])
    return state


def _extract_result(step_results: Dict[int, Any], expected_keys: set) -> Dict[str, Any]:
    for result in step_results.values():
        if isinstance(result, dict) and expected_keys.intersection(result.keys()):
            return result
    return {}
