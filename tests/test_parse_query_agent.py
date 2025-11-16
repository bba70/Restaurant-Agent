import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sub_agents.parse_query.parse_query import (  # noqa: E402
    parse_query_node,
    ParseQueryState,
)


def _build_state(query: str) -> ParseQueryState:
    return ParseQueryState(
        query=query,
        city=None,
        confidence=None,
        reason=None,
        location_source=None,
        error_messages=[],
    )


def test_parse_query_with_city_in_query():
    print("\n=== 测试1: 用户 query 中包含城市 ===")

    mock_response = SimpleNamespace(
        content='{"city": "上海", "confidence": 0.93, "reason": "用户提到了上海"}'
    )

    with patch(
        "sub_agents.parse_query.parse_query.ChatOpenAI"
    ) as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response

        state = _build_state("我在上海，想吃火锅")
        result = parse_query_node(state)

    assert result["city"] == "上海"
    assert result["confidence"] == 0.93
    assert result["location_source"] == "query"
    assert result["error_messages"] == []

    print("✓ 成功识别城市并使用 query 结果")


def test_parse_query_fallback_to_device_location():
    print("\n=== 测试2: query 中无城市，回退到定位 ===")

    mock_response = SimpleNamespace(
        content='{"city": null, "confidence": 0.0, "reason": "未提及城市"}'
    )

    with patch(
        "sub_agents.parse_query.parse_query.ChatOpenAI"
    ) as mock_llm, patch.dict(
        os.environ, {"DEFAULT_CITY": "深圳"}, clear=False
    ):
        mock_llm.return_value.invoke.return_value = mock_response

        state = _build_state("帮我推荐附近的美食")
        result = parse_query_node(state)

    assert result["city"] == "深圳"
    assert result["location_source"] == "device"
    assert result["confidence"] == 1.0

    print("✓ 当 query 无城市信息时，成功使用定位结果")


def test_parse_query_missing_query():
    print("\n=== 测试3: 缺少 query ===")

    with patch(
        "sub_agents.parse_query.parse_query.ChatOpenAI"
    ) as mock_llm:
        state = _build_state("")
        result = parse_query_node(state)
        mock_llm.assert_not_called()

    assert result["city"] is None
    assert any("query 不能为空" in msg for msg in result["error_messages"])

    print("✓ 缺少 query 时直接报错，不调用 LLM")
