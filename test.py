"""
主测试文件：统一调用所有子测试模块
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """运行所有测试"""
    
    print("\n" + "=" * 80)
    print("开始运行所有测试")
    print("=" * 80)
    
    test_results = []
    
    # # 测试2: food_search_agent
    # print("\n" + "-" * 80)
    # print("【测试模块2】food_search_agent 测试")
    # print("-" * 80)
    # try:
    #     from tests.test_food_search_agent import (
    #         test_gaode_poi_search_success,
    #         test_gaode_poi_search_missing_criteria,
    #         test_gaode_poi_search_api_error,
    #         test_gaode_poi_search_network_timeout,
    #         test_gaode_poi_search_missing_api_key,
    #         test_gaode_poi_search_empty_results
    #     )
        
    #     test_gaode_poi_search_success()
    #     test_gaode_poi_search_missing_criteria()
    #     test_gaode_poi_search_api_error()
    #     test_gaode_poi_search_network_timeout()
    #     test_gaode_poi_search_missing_api_key()
    #     test_gaode_poi_search_empty_results()
        
    #     test_results.append(("food_search_agent", "✓ 通过"))
    #     print("\n✓ food_search_agent 测试全部通过")
        
    # except Exception as e:
    #     test_results.append(("food_search_agent", f"✗ 失败: {e}"))
    #     print(f"\n✗ food_search_agent 测试失败: {e}")
    #     import traceback
    #     traceback.print_exc()

    # 测试3: scenario_classifier_agent
    # print("\n" + "-" * 80)
    # print("【测试模块3】scenario_classifier_agent 测试")
    # print("-" * 80)
    # try:
    #     from tests.test_scenario_classifier import (
    #         test_scenario_classifier_success_with_mapping,
    #         test_scenario_classifier_mapping_not_found,
    #         test_scenario_classifier_missing_query,
    #     )

    #     test_scenario_classifier_success_with_mapping()
    #     test_scenario_classifier_mapping_not_found()
    #     test_scenario_classifier_missing_query()

    #     test_results.append(("scenario_classifier_agent", "✓ 通过"))
    #     print("\n✓ scenario_classifier_agent 测试全部通过")

    # except Exception as e:
    #     test_results.append(("scenario_classifier_agent", f"✗ 失败: {e}"))
    #     print(f"\n✗ scenario_classifier_agent 测试失败: {e}")
    #     import traceback
    #     traceback.print_exc()

    # 测试4: parse_query_agent
    # print("\n" + "-" * 80)
    # print("【测试模块4】parse_query_agent 测试")
    # print("-" * 80)
    # try:
    #     from tests.test_parse_query_agent import (
    #         test_parse_query_with_city_in_query,
    #         test_parse_query_fallback_to_device_location,
    #         test_parse_query_missing_query,
    #     )

    #     test_parse_query_with_city_in_query()
    #     test_parse_query_fallback_to_device_location()
    #     test_parse_query_missing_query()

    #     test_results.append(("parse_query_agent", "✓ 通过"))
    #     print("\n✓ parse_query_agent 测试全部通过")

    # except Exception as e:
    #     test_results.append(("parse_query_agent", f"✗ 失败: {e}"))
    #     print(f"\n✗ parse_query_agent 测试失败: {e}")
    #     import traceback
    #     traceback.print_exc()

    # # 打印测试总结
    # print("\n" + "=" * 80)
    # print("测试总结")
    # print("=" * 80)
    
    # for module_name, result in test_results:
    #     print(f"{module_name:30} {result}")
    
    # # 检查是否所有测试都通过
    # all_passed = all("✓" in result for _, result in test_results)
    
    # print("=" * 80)
    # if all_passed:
    #     print("✓ 所有测试通过！")
    #     print("=" * 80)
    #     return 0
    # else:
    #     print("✗ 部分测试失败")
    #     print("=" * 80)
    #     return 1

    # 测试5: orchestrator_flow
    print("\n" + "-" * 80)
    print("【测试模块5】orchestrator_flow 测试")
    print("-" * 80)
    try:
        from tests.test_orchestrator_flow import test_basic_orchestrator_flow

        test_basic_orchestrator_flow()

        test_results.append(("orchestrator_flow", "✓ 通过"))
        print("\n✓ orchestrator_flow 测试全部通过")

    except Exception as e:
        test_results.append(("orchestrator_flow", f"✗ 失败: {e}"))
        print(f"\n✗ orchestrator_flow 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
