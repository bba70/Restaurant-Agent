from plann_and_execute.agent import graph

def test_basic_orchestrator_flow():
    initial_state = {
        "query": "帮我推荐一下陕西科技大学附近的美食",
        "replan_count": 0,
        "error_info": None,
        "past_plans": [],
    }

    final_state = graph.invoke(initial_state)
    print(final_state["final_result"])

if __name__ == "__main__":
    main()