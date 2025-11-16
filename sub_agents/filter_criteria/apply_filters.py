"""
应用筛选条件到搜索结果
"""
from typing import List, Dict, Any, Optional


def apply_filters(
    results: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    对搜索结果应用筛选条件
    
    参数:
        results: 搜索结果列表
        filters: 筛选条件字典，包含：
            - price_range: {"min": int, "max": int}
            - rating_min: float
            - distance_max: int (单位：米)
            - open_now: bool
            - sort_by: str (rating, distance, price, default)
            - sort_order: str (asc, desc)
    
    返回:
        过滤和排序后的结果列表
    """
    
    if not filters:
        filters = {}
    
    filtered_results = results.copy()
    
    # 1. 价格范围筛选
    if "price_range" in filters:
        price_range = filters["price_range"]
        price_min = price_range.get("min", 0)
        price_max = price_range.get("max")
        
        def price_filter(poi: Dict[str, Any]) -> bool:
            cost = poi.get("cost")
            if cost is None:
                return True  # 没有价格信息的保留
            try:
                cost_val = float(cost)
                if cost_val < price_min:
                    return False
                if price_max is not None and cost_val > price_max:
                    return False
                return True
            except (ValueError, TypeError):
                return True
        
        filtered_results = [r for r in filtered_results if price_filter(r)]
        print(f"  > 价格筛选后: {len(filtered_results)} 条结果")
    
    # 2. 评分筛选
    if "rating_min" in filters:
        rating_min = filters["rating_min"]
        
        def rating_filter(poi: Dict[str, Any]) -> bool:
            rating = poi.get("rating")
            if rating is None:
                return True  # 没有评分信息的保留
            try:
                rating_val = float(rating)
                return rating_val >= rating_min
            except (ValueError, TypeError):
                return True
        
        filtered_results = [r for r in filtered_results if rating_filter(r)]
        print(f"  > 评分筛选后: {len(filtered_results)} 条结果")
    
    # 3. 距离筛选
    if "distance_max" in filters:
        distance_max = filters["distance_max"]
        
        def distance_filter(poi: Dict[str, Any]) -> bool:
            # 注意：这里需要计算实际距离，但高德API返回的是相对位置
            # 简化处理：假设结果已按距离排序，保留前N个
            # 实际应用中需要计算两点间距离
            return True
        
        # 由于高德API已按距离排序，这里只保留前distance_max/1000个结果
        # 这是一个简化的处理方式
        max_count = max(1, distance_max // 1000)
        filtered_results = filtered_results[:max_count]
        print(f"  > 距离筛选后: {len(filtered_results)} 条结果")
    
    # 4. 排序
    sort_by = filters.get("sort_by", "default")
    sort_order = filters.get("sort_order", "desc")
    
    if sort_by == "rating":
        def get_rating(poi):
            try:
                return float(poi.get("rating", 0))
            except (ValueError, TypeError):
                return 0
        
        filtered_results.sort(
            key=get_rating,
            reverse=(sort_order == "desc")
        )
        print(f"  > 按评分排序（{sort_order}）")
    
    elif sort_by == "price":
        def get_price(poi):
            try:
                return float(poi.get("cost", 0))
            except (ValueError, TypeError):
                return 0
        
        filtered_results.sort(
            key=get_price,
            reverse=(sort_order == "desc")
        )
        print(f"  > 按价格排序（{sort_order}）")
    
    elif sort_by == "distance":
        # 高德API已按距离排序，这里只需要反序如果需要
        if sort_order == "asc":
            # 保持原顺序（已按距离升序）
            pass
        else:
            filtered_results.reverse()
        print(f"  > 按距离排序（{sort_order}）")
    
    return filtered_results


def filter_and_sort_results(
    results: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    对搜索结果进行完整的筛选和排序
    
    返回:
        包含过滤结果和统计信息的字典
    """
    
    original_count = len(results)
    filtered_results = apply_filters(results, filters)
    filtered_count = len(filtered_results)
    
    return {
        "search_results": filtered_results,
        "original_count": original_count,
        "filtered_count": filtered_count,
        "filters_applied": filters or {},
    }
