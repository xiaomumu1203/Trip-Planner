"""高德地图服务 —— 直接调用高德 REST API"""

import json
import httpx
from typing import List, Dict, Any, Optional
from ..config import get_settings
from ..models.schemas import Location


class AmapService:
    """高德地图服务封装"""

    BASE_URL = "https://restapi.amap.com/v3"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.amap_api_key
        if not self.api_key:
            raise ValueError("高德地图 API Key 未配置，请在.env文件中设置AMAP_API_KEY")
        print(f"✅ 高德地图服务初始化成功")

    def _parse_location(self, location_str: str) -> dict:
        """解析高德经纬度字符串（"116.397,39.907" → {"longitude": 116.397, "latitude": 39.907}）"""
        lng, lat = 0, 0
        if "," in location_str:
            parts = location_str.split(",")
            try:
                lng, lat = float(parts[0]), float(parts[1])
            except ValueError:
                pass
        return {"longitude": lng, "latitude": lat}

    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> list:
        """
        搜索 POI

        高德 API：https://restapi.amap.com/v3/place/text
        """
        try:
            params = {
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "key": self.api_key,
                "offset": 20,
            }
            resp = httpx.get(f"{self.BASE_URL}/place/text", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "1":
                print(f"⚠️ 高德 POI 搜索失败: {data.get('info', '未知错误')}")
                return []

            pois = data.get("pois", [])
            print(f"POI搜索结果: 找到 {len(pois)} 个POI")

            formatted = []
            for poi in pois:
                loc = self._parse_location(poi.get("location", ""))
                formatted.append({
                    "id": poi.get("id", ""),
                    "name": poi.get("name", ""),
                    "type": poi.get("type", ""),
                    "address": poi.get("address", ""),
                    "location": loc,
                    "tel": poi.get("tel", ""),
                    "distance": poi.get("distance", ""),
                    "rating": poi.get("biz_ext", {}).get("rating", ""),
                    "cost": poi.get("biz_ext", {}).get("cost", ""),
                })

            return formatted

        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []

    def get_weather(self, city: str) -> dict:
        """
        查询天气

        高德 API：https://restapi.amap.com/v3/weather/weatherInfo
        """
        try:
            params = {
                "city": city,
                "key": self.api_key,
                "extensions": "all",
            }
            resp = httpx.get(f"{self.BASE_URL}/weather/weatherInfo", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "1":
                print(f"⚠️ 天气查询失败: {data.get('info', '未知错误')}")
                return {"casts": []}

            forecasts = data.get("forecasts", [])
            casts = []
            for forecast in forecasts:
                casts.extend(forecast.get("casts", []))

            print(f"天气查询结果: 获取到 {len(casts)} 天天气")
            return {"casts": casts}

        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return {"casts": []}

    def plan_route(self, origin: str, destination: str,
                   origin_city: str = "", destination_city: str = "",
                   route_type: str = "walking") -> dict:
        """
        路线规划

        高德 API：https://restapi.amap.com/v3/direction/{type}
        """
        type_map = {
            "walking": "walking",
            "driving": "driving",
            "transit": "transit/integrated",
        }
        api_type = type_map.get(route_type, "walking")

        try:
            params = {
                "key": self.api_key,
                "origin": origin,
                "destination": destination,
            }
            if route_type == "transit":
                if origin_city:
                    params["city"] = origin_city
                if destination_city:
                    params["cityd"] = destination_city

            resp = httpx.get(f"{self.BASE_URL}/direction/{api_type}", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            print(f"路线规划结果: 状态={data.get('status', 'unknown')}")
            return data

        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}

    def geocode(self, address: str, city: str = "") -> Optional[Location]:
        """
        地理编码（地址转坐标）

        高德 API：https://restapi.amap.com/v3/geocode/geo
        """
        try:
            params = {"address": address, "key": self.api_key}
            if city:
                params["city"] = city

            resp = httpx.get(f"{self.BASE_URL}/geocode/geo", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == "1" and data.get("geocodes"):
                geocode = data["geocodes"][0]
                loc = self._parse_location(geocode.get("location", ""))
                return Location(longitude=loc["longitude"], latitude=loc["latitude"])

            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> dict:
        """
        获取 POI 详情

        高德 API：https://restapi.amap.com/v3/place/detail
        """
        try:
            params = {"id": poi_id, "key": self.api_key}
            resp = httpx.get(f"{self.BASE_URL}/place/detail", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            print(f"POI详情结果: 状态={data.get('status', 'unknown')}")
            return data

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service
    if _amap_service is None:
        _amap_service = AmapService()
    return _amap_service
