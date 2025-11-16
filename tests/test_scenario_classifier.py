import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sub_agents.scenario_classifier.scenario_classifier import (  # noqa: E402
    scenario_classifier_node,
    ScenarioClassifierState,
)


def _build_state(query: str) -> ScenarioClassifierState:
    return ScenarioClassifierState(
        query=query,
        scenario=None,
        restaurant_type=None,
        confidence=None,
        error_messages=[],
    )


def test_scenario_classifier_success_with_mapping():
    print("\n=== 测试1: 成功识别场景并映射 type ===")

    mock_response = SimpleNamespace(
        content='{"scenario": "火锅", "confidence": 0.92}'
    )

    with patch(
        "sub_agents.scenario_classifier.scenario_classifier.ChatOpenAI"
    ) as mock_llm, patch(
        "sub_agents.scenario_classifier.scenario_classifier.TAXONOMY_MAP",
        {"火锅": {"medium_category": "火锅", "small_category": None, "type": "050400"}},
    ):
        mock_llm.return_value.invoke.return_value = mock_response

        state = _build_state("想吃火锅")
        result = scenario_classifier_node(state)

    assert result["scenario"] == "火锅"
    assert result["restaurant_type"] == "050400"
    assert result["confidence"] == 0.92
    assert result["error_messages"] == []

    print("✓ 场景识别成功，并正确映射为 050400")


def test_scenario_classifier_mapping_not_found():
    print("\n=== 测试2: 场景识别成功但映射缺失 ===")

    mock_response = SimpleNamespace(
        content='{"scenario": "未知菜系", "confidence": 0.8}'
    )

    with patch(
        "sub_agents.scenario_classifier.scenario_classifier.ChatOpenAI"
    ) as mock_llm, patch(
        "sub_agents.scenario_classifier.scenario_classifier.TAXONOMY_MAP",
        {},
    ):
        mock_llm.return_value.invoke.return_value = mock_response

        state = _build_state("我想吃一种未在映射表中的菜")
        result = scenario_classifier_node(state)

    assert result["scenario"] == "未知菜系"
    assert result["restaurant_type"] is None
    assert result["confidence"] == 0.8

    print("✓ 当映射缺失时，restaurant_type 为 None")


def test_scenario_classifier_missing_query():
    print("\n=== 测试3: 缺少 query 输入 ===")

    with patch(
        "sub_agents.scenario_classifier.scenario_classifier.ChatOpenAI"
    ) as mock_llm:
        state = _build_state("")
        result = scenario_classifier_node(state)

        mock_llm.assert_not_called()

    assert len(result["error_messages"]) > 0
    assert "query 不能为空" in result["error_messages"][0]
    assert result["scenario"] is None
    assert result["restaurant_type"] is None

    print("✓ 缺少 query 时，不调用 LLM 并返回错误信息")
