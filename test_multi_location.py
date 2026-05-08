"""
集成测试：multi-location-equidistant-search
验证完整编排流程、端到端行为和 API 响应结构
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock

# 测试用例
TESTS = [
    {
        "name": "7.1 双地点等距 query",
        "query": "我和朋友分别在天安门和望京，找个中间位置的火锅",
        "expect": {
            "search_mode": "intersection",
            "location_count": 2,
            "has_recommendations_hard": True,
            "has_recommendations_soft": True,
        }
    },
    {
        "name": "7.2 交集为空的降级测试",
        "query": "我在天安门和望京找一家只有这家有的餐厅",
        "expect": {
            "search_mode": "intersection",
            "location_count": 2,
            "fallback_maybe": True,
        }
    },
    {
        "name": "7.3 单地点向后兼容",
        "query": "北京附近有什么好吃的",
        "expect": {
            "search_mode": "single",
            "location_count": 1,
            "has_locations": True,
        }
    },
    {
        "name": "7.4 三地点 query",
        "query": "我们在国贸、三里屯、西单之间找个吃饭的地方",
        "expect": {
            "search_mode": "intersection",
            "location_count": 3,
            "has_recommendations": True,
        }
    },
    {
        "name": "7.5 hard vs soft 模式差异验证",
        "query": "我和朋友在天安门和望京之间找个火锅店",
        "expect": {
            "search_mode": "intersection",
            "recommendations_hard_count": 5,
            "recommendations_soft_count": 5,
            "modes_differ": True,
        }
    },
]


def run_test(test_def, use_mock=True):
    """运行单个测试"""
    from plann_and_execute.agent import graph

    name = test_def["name"]
    query = test_def["query"]
    expect = test_def["expect"]

    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"query: {query}")
    print(f"{'='*60}")

    try:
        initial_state = {
            "query": query,
            "replan_count": 0,
            "error_info": None,
            "past_plans": [],
        }
        final_state = graph.invoke(initial_state)

        result_str = final_state.get("final_result", "{}")
        result = json.loads(result_str)

        # 打印结果摘要
        print(f"  search_mode: {result.get('search_mode')}")
        print(f"  location_count: {result.get('location_count')}")
        print(f"  locations: {json.dumps(result.get('locations', []), ensure_ascii=False)}")
        print(f"  fallback: {result.get('fallback')}")
        hard = result.get("recommendations_hard", [])
        soft = result.get("recommendations_soft", [])
        print(f"  recommendations_hard: {len(hard)} 条")
        print(f"  recommendations_soft: {len(soft)} 条")
        if hard:
            print(f"  hard[0]: {hard[0].get('name')} (rating: {hard[0].get('rating')})")
        if soft:
            print(f"  soft[0]: {soft[0].get('name')} (rating: {soft[0].get('rating')})")

        # 验证断言
        ok = True
        for key, val in expect.items():
            if key == "has_recommendations_hard":
                actual = len(hard) > 0
                if actual != val:
                    print(f"  [FAIL] 期望 recommendations_hard 非空，实际: {len(hard)}")
                    ok = False
            elif key == "has_recommendations_soft":
                actual = len(soft) > 0
                if actual != val:
                    print(f"  [FAIL] 期望 recommendations_soft 非空，实际: {len(soft)}")
                    ok = False
            elif key == "has_recommendations":
                actual = (len(hard) > 0 or len(soft) > 0)
                if actual != val:
                    print(f"  [FAIL] 期望有推荐结果")
                    ok = False
            elif key == "fallback_maybe":
                # fallback 可能为 null 或 "midpoint"
                actual_fb = result.get("fallback")
                if actual_fb not in (None, "midpoint"):
                    print(f"  [FAIL] 期望 fallback 为 null 或 midpoint，实际: {actual_fb}")
                    ok = False
            elif key == "modes_differ":
                actual = (hard != soft) and (len(hard) == len(soft))
                if not actual:
                    print(f"  [FAIL] 期望 hard 和 soft 结果不同但数量相同")
                    ok = False
            elif key == "recommendations_hard_count":
                if len(hard) != val:
                    print(f"  [FAIL] 期望 hard {val} 条，实际: {len(hard)}")
                    ok = False
            elif key == "recommendations_soft_count":
                if len(soft) != val:
                    print(f"  [FAIL] 期望 soft {val} 条，实际: {len(soft)}")
                    ok = False
            else:
                actual = result.get(key)
                if actual != val:
                    print(f"  [FAIL] 期望 {key}={val}，实际: {actual}")
                    ok = False

        if ok:
            print(f"  ✓ PASS")
        else:
            print(f"  ✗ FAIL")
        return ok, result

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def main():
    print(f"集成测试: multi-location-equidistant-search")
    print(f"用例数: {len(TESTS)}")

    passed = 0
    failed = 0
    for test_def in TESTS:
        ok, _ = run_test(test_def)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"汇总: {passed}/{len(TESTS)} 通过, {failed} 失败")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
