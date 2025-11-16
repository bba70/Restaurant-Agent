from plann_and_execute.state import OrchestratorState
from langgraph.graph import StateGraph, START, END
from plann_and_execute.node import planner_node, executor_node, subgraph_node, formatter_node

def route_after_subgraph_execution(state: OrchestratorState) -> str:
    """
    在子图执行后，决定下一步的走向。
    
    逻辑:
    1. 如果有错误信息，检查是否需要重规划或终止
    2. 如果当前步骤超过计划总步数，表示计划完成
    3. 否则继续执行下一步
    
    可能的输出:
    - 'replan': 发生错误，返回planner节点进行重规划。
    - 'continue': 计划未完成，继续执行下一步。
    - 'end': 计划已成功完成。
    - 'error': 发生致命错误或重试次数超出限制。
    """
    
    plan = state.get("plan")
    current_step = state.get("current_step", 0)
    error_info = state.get("error_info")
    replan_count = state.get("replan_count", 0)
    
    print(f"\n--- 路由判断 ---")
    print(f"当前步骤: {current_step}")
    print(f"计划总步数: {len(plan.steps) if plan else 0}")
    print(f"错误信息: {error_info}")
    print(f"重规划次数: {replan_count}")
    
    # 检查是否所有步骤都已完成（在检查错误之前）
    if plan and current_step > len(plan.steps):
        print(f"所有步骤已完成，进入格式化阶段")
        return "end"
    
    # 检查是否有执行错误
    if error_info is not None:
        print(f"检测到错误: {error_info.get('error_type')}")
        
        # 检查重试次数是否超出限制（最多重试3次）
        MAX_REPLAN_COUNT = 3
        if replan_count >= MAX_REPLAN_COUNT:
            print(f"重规划次数已达上限 ({MAX_REPLAN_COUNT})，终止执行")
            return "error"
        
        # 某些错误类型不可恢复，直接终止
        unrecoverable_errors = ["OUT_OF_RANGE", "PARSE_ERROR"]
        if error_info.get("error_type") in unrecoverable_errors:
            print(f"不可恢复的错误类型: {error_info.get('error_type')}")
            return "error"
        
        # 其他错误进行重规划
        print(f"触发重规划")
        state["replan_count"] = replan_count + 1
        return "replan"
    
    # 检查是否所有步骤都已完成
    if plan and current_step > len(plan.steps):
        print(f"所有步骤已完成，进入格式化阶段")
        return "end"
    
    # 计划未完成，继续执行下一步
    print(f"计划未完成，继续执行下一步")
    return "continue"
    
workflow = StateGraph(OrchestratorState)

workflow.add_node("planner", planner_node)
workflow.add_node("subgraph", subgraph_node)
workflow.add_node("executor", executor_node)
workflow.add_node("formatter", formatter_node)

workflow.set_entry_point("planner")

workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "subgraph")
workflow.add_edge("formatter", END)

workflow.add_conditional_edges(
    source="subgraph",
    path=route_after_subgraph_execution,
    path_map={
        # 如果计划未完成，返回`executor`去分发下一步任务
        "continue": "executor",
        # 如果执行失败，返回`planner`进行重规划
        "replan": "planner",
        # 如果计划已成功完成，进入`formatter`进行总结
        "end": "formatter",
        # 如果发生不可恢复的错误，直接结束
        "error": END
    }
)

graph = workflow.compile()


