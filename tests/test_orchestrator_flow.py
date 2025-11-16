from plann_and_execute.agent import graph

def test_basic_orchestrator_flow():
    initial_state = {
        "query": "我在北京想吃川菜，有没有推荐？",
        "replan_count": 0,
        "error_info": None,
        "past_plans": [],
    }

    final_state = graph.invoke(initial_state)
    print(final_state["final_result"])

if __name__ == "__main__":
    main()