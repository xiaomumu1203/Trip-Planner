"""工具定义 —— OpenAI Function Calling Schema + 工具映射"""

# ============ 工具 Schema（OpenAI Function Calling 格式）============

TOOL_SEARCH_POI = {
    "type": "function",
    "function": {
        "name": "search_poi",
        "description": "搜索指定城市的POI（景点、酒店、餐厅等兴趣点），返回名称、地址、坐标、评分等信息",
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "搜索关键词，如'历史文化''自然风光''经济型酒店'"},
                "city": {"type": "string", "description": "城市名称，如'北京''上海'"},
            },
            "required": ["keywords", "city"]
        }
    }
}

TOOL_GET_WEATHER = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气预报，返回每日天气、温度、风力等信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如'北京'"},
            },
            "required": ["city"]
        }
    }
}

# 工具分组
ATTRACTION_HOTEL_TOOLS = [TOOL_SEARCH_POI]
WEATHER_TOOLS = [TOOL_GET_WEATHER]


def create_tool_map(amap_service):
    """
    根据 AMap 服务实例创建工具名称到实际函数的映射

    Args:
        amap_service: AmapService 实例

    Returns:
        dict: {工具名: 可调用函数}
    """
    return {
        "search_poi": lambda keywords, city: amap_service.search_poi(keywords=keywords, city=city),
        "get_weather": lambda city: amap_service.get_weather(city),
    }
