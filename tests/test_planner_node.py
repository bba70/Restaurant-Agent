"""
测试 planner_node 节点
"""
import json
from plann_and_execute.state import OrchestratorState
from plann_and_execute.node import planner_node


def test_planner_node_basic():
    """测试基础的美食推荐规划"""
    
    # 初始化state
    state: OrchestratorState = {
        "query": "帮我推荐附近有哪些美食",
        "plan": None,
        "past_plans": [],
        "current_step": 0,
        "step_results": {},
        "error_info": None,
        "replan_count": 0,
        "final_result": ""
    }
    
    print("=" * 60)
    print("测试1: 基础美食推荐规划")
    print("=" * 60)
    print(f"用户查询: {state['query']}\n")
    
    # 执行planner_node
    result_state = planner_node(state)
    
    # 验证结果
    assert result_state["plan"] is not None, "计划不能为空"
    assert len(result_state["plan"].steps) > 0, "计划步骤不能为空"
    assert result_state["current_step"] == 1, "当前步骤应该是1"
    
    print("\n✓ 规划成功!")
    print(f"生成的计划步骤数: {len(result_state['plan'].steps)}\n")

    print(result_state)
    
    # 打印详细的计划信息
    # for step in result_state["plan"].steps:
    #     print(f"Step {step.step_id}: {step.subgraph_name}")
    #     print(f"  描述: {step.description}")
    #     if step.input_mapping:
    #         print(f"  输入映射: {step.input_mapping}")
    #     print()


def test_planner_node_with_preferences():
    """测试带有具体偏好的美食推荐规划"""
    
    state: OrchestratorState = {
        "query": "我在北京，想吃川菜，预算200块钱以内，评分要4.5分以上",
        "plan": None,
        "past_plans": [],
        "current_step": 0,
        "step_results": {},
        "error_info": None,
        "replan_count": 0,
        "final_result": ""
    }
    
    print("=" * 60)
    print("测试2: 带有具体偏好的美食推荐规划")
    print("=" * 60)
    print(f"用户查询: {state['query']}\n")
    
    result_state = planner_node(state)
    
    assert result_state["plan"] is not None
    assert len(result_state["plan"].steps) > 0
    
    print("\n✓ 规划成功!")
    print(f"生成的计划步骤数: {len(result_state['plan'].steps)}\n")
    
    for step in result_state["plan"].steps:
        print(f"Step {step.step_id}: {step.subgraph_name}")
        print(f"  描述: {step.description}")
        if step.input_mapping:
            print(f"  输入映射: {step.input_mapping}")
        print()


def test_planner_node_replan():
    """测试重规划场景"""
    
    state: OrchestratorState = {
        "query": "帮我推荐附近有哪些美食",
        "plan": None,
        "past_plans": [
            json.dumps({
                "steps": [
                    {
                        "step_id": 1,
                        "subgraph_name": "search_restaurants",
                        "description": "搜索附近餐厅",
                        "input_mapping": None
                    }
                ]
            })
        ],
        "current_step": 0,
        "step_results": {},
        "error_info": {
            "error_type": "API_ERROR",
            "message": "搜索接口超时",
            "step": 1
        },
        "replan_count": 1,
        "final_result": ""
    }
    
    print("=" * 60)
    print("测试3: 重规划场景")
    print("=" * 60)
    print(f"用户查询: {state['query']}")
    print(f"重试次数: {state['replan_count']}")
    print(f"错误信息: {state['error_info']}\n")
    
    result_state = planner_node(state)
    
    assert result_state["plan"] is not None
    assert len(result_state["plan"].steps) > 0
    assert len(result_state["past_plans"]) == 2, "应该记录新的计划"
    
    print("\n✓ 重规划成功!")
    print(f"生成的计划步骤数: {len(result_state['plan'].steps)}\n")
    
    for step in result_state["plan"].steps:
        print(f"Step {step.step_id}: {step.subgraph_name}")
        print(f"  描述: {step.description}")
        if step.input_mapping:
            print(f"  输入映射: {step.input_mapping}")
        print()


def test_plan_output_format():
    """验证计划输出格式"""
    
    state: OrchestratorState = {
        "query": "推荐附近的美食",
        "plan": None,
        "past_plans": [],
        "current_step": 0,
        "step_results": {},
        "error_info": None,
        "replan_count": 0,
        "final_result": ""
    }
    
    print("=" * 60)
    print("测试4: 验证计划输出格式")
    print("=" * 60)
    
    result_state = planner_node(state)
    plan = result_state["plan"]
    
    # 验证Plan对象结构
    assert hasattr(plan, "steps"), "Plan应该有steps属性"
    assert isinstance(plan.steps, list), "steps应该是列表"
    
    # 验证每个PlanStep的结构
    for i, step in enumerate(plan.steps):
        assert hasattr(step, "step_id"), f"Step {i}缺少step_id"
        assert hasattr(step, "subgraph_name"), f"Step {i}缺少subgraph_name"
        assert hasattr(step, "description"), f"Step {i}缺少description"
        assert hasattr(step, "input_mapping"), f"Step {i}缺少input_mapping"
        
        # 验证step_id连续性
        assert step.step_id == i + 1, f"Step ID应该从1开始连续递增"
        
        # 验证字段类型
        assert isinstance(step.step_id, int), f"step_id应该是整数"
        assert isinstance(step.subgraph_name, str), f"subgraph_name应该是字符串"
        assert isinstance(step.description, str), f"description应该是字符串"
        assert step.input_mapping is None or isinstance(step.input_mapping, dict), \
            f"input_mapping应该是None或字典"
    
    print("✓ 所有格式验证通过!")
    print(f"  - Plan有{len(plan.steps)}个步骤")
    print(f"  - 所有step_id连续递增")
    print(f"  - 所有字段类型正确")


if __name__ == "__main__":
    try:
        test_planner_node_basic()
        print("\n" + "=" * 60 + "\n")
        
        #test_planner_node_with_preferences()
        #print("\n" + "=" * 60 + "\n")
        
        #test_planner_node_replan()
        #print("\n" + "=" * 60 + "\n")
        
        #test_plan_output_format()
        #print("\n" + "=" * 60)
        #print("✓ 所有测试通过!")
        #print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
