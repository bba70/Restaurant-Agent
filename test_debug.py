import sys
sys.path.insert(0, r'D:\desktop\Food')

from plann_and_execute.state import OrchestratorState
from plann_and_execute.agent import graph

# 测试查询
test_query = "陕西科技大学附近的火锅"

initial_state = OrchestratorState(
    query=test_query,
    replan_count=0,
    error_info=None,
    past_plans=[],
)

print(f"测试查询: {test_query}\n")
final_state = graph.invoke(initial_state)

print("\n最终结果:")
import json
result_str = final_state.get('final_result', '{}')
result = json.loads(result_str)
print(json.dumps(result, ensure_ascii=False, indent=2))
