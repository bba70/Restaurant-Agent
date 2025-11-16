import os
import sys
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sub_agents.food_search.food_search import gaode_poi_search_node, FoodSearchState


def test_gaode_poi_search_success():
    """测试高德POI搜索成功的情况"""
    print("\n=== 测试1: 高德POI搜索成功 ===")
    
    # 模拟高德API的成功响应
    mock_response = {
        "status": "1",
        "info": "OK",
        "pois": [
            {
                "name": "老舍茶馆",
                "address": "北京市东城区前门西大街",
                "location": "116.401,39.901",
                "tel": "010-63036830",
                "type": "050000",
                "biz_ext": {
                    "rating": "4.5",
                    "cost": "100"
                }
            },
            {
                "name": "全聚德",
                "address": "北京市东城区前门大街",
                "location": "116.402,39.902",
                "tel": "010-67011379",
                "type": "050000",
                "biz_ext": {
                    "rating": "4.6",
                    "cost": "200"
                }
            }
        ]
    }
    
    # 初始化状态
    state: FoodSearchState = {
        "search_criteria": {
            "keywords": "烤鸭",
            "location": "116.4,39.9",
            "city": "北京"
        },
        "search_results": [],
        "error_messages": []
    }
    
    # 模拟requests.get
    with patch('sub_agents.food_search.food_search.requests.get') as mock_get:
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_get.return_value = mock_response_obj
        
        # 设置环境变量
        with patch.dict(os.environ, {"GAODE_API_KEY": "test_key"}):
            result = gaode_poi_search_node(state)
    
    # 验证结果
    assert len(result["search_results"]) == 2, f"期望2条结果，实际{len(result['search_results'])}"
    assert result["search_results"][0]["name"] == "老舍茶馆", "第一条结果名称不匹配"
    assert result["search_results"][0]["rating"] == "4.5", "评分不匹配"
    assert len(result["error_messages"]) == 0, f"不应该有错误，但有: {result['error_messages']}"
    
    print("✓ 测试通过: 成功获取2条餐厅信息")
    print(f"  结果: {json.dumps(result['search_results'], ensure_ascii=False, indent=2)}")


def test_gaode_poi_search_missing_criteria():
    """测试缺少搜索条件的情况"""
    print("\n=== 测试2: 缺少搜索条件 ===")
    
    # 缺少location
    state: FoodSearchState = {
        "search_criteria": {
            "keywords": "烤鸭"
        },
        "search_results": [],
        "error_messages": []
    }
    
    with patch.dict(os.environ, {"GAODE_API_KEY": "test_key"}):
        result = gaode_poi_search_node(state)
    
    # 验证结果
    assert len(result["error_messages"]) > 0, "应该有错误信息"
    assert "search_criteria 必须包含" in result["error_messages"][0], "错误信息不正确"
    assert len(result["search_results"]) == 0, "不应该有搜索结果"
    
    print("✓ 测试通过: 正确捕获缺少条件的错误")
    print(f"  错误信息: {result['error_messages'][0]}")


def test_gaode_poi_search_api_error():
    """测试高德API返回业务错误的情况"""
    print("\n=== 测试3: 高德API业务错误 ===")
    
    # 模拟高德API的错误响应
    mock_response = {
        "status": "0",
        "info": "INVALID_USER_KEY",
        "pois": []
    }
    
    state: FoodSearchState = {
        "search_criteria": {
            "keywords": "烤鸭",
            "location": "116.4,39.9"
        },
        "search_results": [],
        "error_messages": []
    }
    
    with patch('sub_agents.food_search.food_search.requests.get') as mock_get:
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_get.return_value = mock_response_obj
        
        with patch.dict(os.environ, {"GAODE_API_KEY": "test_key"}):
            result = gaode_poi_search_node(state)
    
    # 验证结果
    assert len(result["error_messages"]) > 0, "应该有错误信息"
    assert "高德API业务错误" in result["error_messages"][0], "错误信息不正确"
    
    print("✓ 测试通过: 正确捕获API业务错误")
    print(f"  错误信息: {result['error_messages'][0]}")


def test_gaode_poi_search_network_timeout():
    """测试网络超时的情况"""
    print("\n=== 测试4: 网络超时 ===")
    
    import requests
    
    state: FoodSearchState = {
        "search_criteria": {
            "keywords": "烤鸭",
            "location": "116.4,39.9"
        },
        "search_results": [],
        "error_messages": []
    }
    
    with patch('sub_agents.food_search.food_search.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        with patch.dict(os.environ, {"GAODE_API_KEY": "test_key"}):
            result = gaode_poi_search_node(state)
    
    # 验证结果
    assert len(result["error_messages"]) > 0, "应该有错误信息"
    assert "超时" in result["error_messages"][0], "错误信息应该包含超时"
    
    print("✓ 测试通过: 正确捕获网络超时")
    print(f"  错误信息: {result['error_messages'][0]}")


def test_gaode_poi_search_missing_api_key():
    """测试缺少API密钥的情况"""
    print("\n=== 测试5: 缺少API密钥 ===")
    
    state: FoodSearchState = {
        "search_criteria": {
            "keywords": "烤鸭",
            "location": "116.4,39.9"
        },
        "search_results": [],
        "error_messages": []
    }
    
    # 确保GAODE_API_KEY不存在
    with patch.dict(os.environ, {}, clear=True):
        try:
            result = gaode_poi_search_node(state)
            assert False, "应该抛出EnvironmentError"
        except EnvironmentError as e:
            assert "GAODE_API_KEY" in str(e), "错误信息应该包含GAODE_API_KEY"
            print("✓ 测试通过: 正确抛出EnvironmentError")
            print(f"  错误信息: {e}")


def test_gaode_poi_search_empty_results():
    """测试搜索结果为空的情况"""
    print("\n=== 测试6: 搜索结果为空 ===")
    
    # 模拟高德API返回空结果
    mock_response = {
        "status": "1",
        "info": "OK",
        "pois": []
    }
    
    state: FoodSearchState = {
        "search_criteria": {
            "keywords": "某个不存在的餐厅",
            "location": "116.4,39.9"
        },
        "search_results": [],
        "error_messages": []
    }
    
    with patch('sub_agents.food_search.food_search.requests.get') as mock_get:
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_get.return_value = mock_response_obj
        
        with patch.dict(os.environ, {"GAODE_API_KEY": "test_key"}):
            result = gaode_poi_search_node(state)
    
    # 验证结果
    assert len(result["search_results"]) == 0, "应该没有搜索结果"
    assert len(result["error_messages"]) == 0, "不应该有错误信息"
    
    print("✓ 测试通过: 正确处理空结果")
    print(f"  搜索结果数: {len(result['search_results'])}")


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试高德美食搜索Agent")
    print("=" * 60)
    
    try:
        test_gaode_poi_search_success()
        test_gaode_poi_search_missing_criteria()
        test_gaode_poi_search_api_error()
        test_gaode_poi_search_network_timeout()
        test_gaode_poi_search_missing_api_key()
        test_gaode_poi_search_empty_results()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
