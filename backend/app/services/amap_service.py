"""AMap POI service with MCP-first lookup and REST fallback."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Dict, List

import requests

from app.config import get_settings
from app.services.mcp_service import MCPToolService

logger = logging.getLogger(__name__)


class AMapService:
    """Wrapper around AMap place APIs."""

    _cache: Dict[str, List[Dict]] = {}
    _city_code_cache: Dict[str, str] = {}
    _request_lock = threading.Lock()
    _last_request_ts = 0.0
    _min_request_interval = 0.35

    def __init__(self):
        self.settings = get_settings()
        self.api_key = (self.settings.amap_api_key or "").strip()
        self.base_url = "https://restapi.amap.com/v3"
        self.timeout = 4
        self.disabled = not bool(self.api_key)
        self.use_mcp = bool(self.settings.use_amap_mcp)
        self.mcp_service = MCPToolService() if self.use_mcp else None
        if self.disabled:
            logger.info("AMapService disabled because amap_api_key is missing")

    def search_poi(self, keywords: str, city: str, poi_type: str = "", limit: int = 5) -> List[Dict]:
        """Search points of interest and return normalized results."""
        if self.disabled:
            return []

        normalized_keywords = (keywords or "").strip()
        normalized_city = (city or "").strip()
        city_token = self._resolve_city_token(normalized_city) or normalized_city
        cache_key = f"{city_token}|{normalized_keywords}|{poi_type}|{limit}"
        if cache_key in AMapService._cache:
            return list(AMapService._cache[cache_key])

        mcp_results = self._search_poi_via_mcp(normalized_keywords, normalized_city, limit)
        if mcp_results:
            deduped = self._dedupe(mcp_results)[:limit]
            AMapService._cache[cache_key] = list(deduped)
            return deduped

        rest_results = self._search_poi_via_rest(normalized_keywords, city_token, poi_type, limit)
        if rest_results:
            AMapService._cache[cache_key] = list(rest_results)
        return rest_results

    def search_attractions(self, city: str) -> List[Dict]:
        if self.disabled:
            return []

        target_pool = 18
        queries = [
            f"{city}景点",
            f"{city}公园",
            f"{city}博物馆",
            f"{city}广场",
            f"{city}海洋公园",
            f"{city}历史街区",
            f"{city}步道",
            f"{city}山",
            f"{city}地标",
        ]

        result: List[Dict] = []
        for keyword in queries:
            result.extend(self.search_poi(keyword, city, "", limit=12))
            if len(self._dedupe(result)) >= target_pool:
                break
        return self._dedupe(result)[:target_pool]

    def search_hotels(self, city: str, accommodation_type: str = "酒店") -> List[Dict]:
        if self.disabled:
            return []

        keywords_map = {
            "经济型酒店": f"{city}经济型酒店",
            "商务酒店": f"{city}商务酒店",
            "精品酒店": f"{city}精品酒店",
            "民宿": f"{city}民宿",
            "豪华酒店": f"{city}豪华酒店",
        }
        keyword = keywords_map.get(accommodation_type, f"{city}{accommodation_type or '酒店'}")
        result = self.search_poi(keyword, city, "", limit=12)
        if len(result) < 5:
            result.extend(self.search_poi(f"{city}酒店", city, "", limit=12))
        return self._dedupe(result)[:10]

    def search_restaurants(self, city: str) -> List[Dict]:
        if self.disabled:
            return []

        result: List[Dict] = []
        queries = [
            f"{city}餐厅",
            f"{city}美食",
            f"{city}小吃",
            f"{city}特色菜",
            f"{city}早餐",
            f"{city}晚餐",
        ]
        for keyword in queries:
            result.extend(self.search_poi(keyword, city, "", limit=12))
            if len(self._dedupe(result)) >= 20:
                break
        return self._dedupe(result)[:20]

    def _search_poi_via_mcp(self, keywords: str, city: str, limit: int) -> List[Dict]:
        if not self.mcp_service:
            return []
        try:
            raw_items = self.mcp_service.search_poi(keywords, city)
            formatted = [self._format_poi(item) for item in raw_items if isinstance(item, dict)]
            formatted = [item for item in formatted if item.get("name")]
            if formatted:
                logger.info("AMap MCP POI hit for %s in %s: %s items", keywords, city, len(formatted))
            return self._dedupe(formatted)[:limit]
        except Exception as exc:
            logger.info("AMap MCP POI search failed for %s in %s: %s", keywords, city, exc)
            return []

    def _search_poi_via_rest(self, keywords: str, city_token: str, poi_type: str, limit: int) -> List[Dict]:
        try:
            url = f"{self.base_url}/place/text"
            params = {
                "key": self.api_key,
                "keywords": keywords,
                "city": city_token,
                "citylimit": "true" if city_token else "false",
                "types": poi_type,
                "extensions": "all",
                "output": "json",
                "offset": max(limit, 10),
                "page": 1,
            }
            with AMapService._request_lock:
                now = time.monotonic()
                wait_seconds = AMapService._min_request_interval - (now - AMapService._last_request_ts)
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                response = requests.get(url, params=params, timeout=self.timeout)
                AMapService._last_request_ts = time.monotonic()

            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                info = data.get("info", "unknown error")
                if info in {"CUQPS_HAS_EXCEEDED_THE_LIMIT", "DAILY_QUERY_OVER_LIMIT", "ACCESS_TOO_FREQUENT"}:
                    logger.warning("AMap POI search hit rate limit, keeping last cache for %s|%s: %s", city_token, keywords, info)
                else:
                    logger.warning("AMap POI search failed: %s", info)
                return []

            formatted = [self._format_poi(poi) for poi in (data.get("pois", []) or [])]
            formatted = [item for item in formatted if item.get("name")]
            return self._dedupe(formatted)[:limit]
        except Exception as exc:
            logger.warning("AMap POI search exception for %s|%s: %s", city_token, keywords, exc)
            return []

    def _resolve_city_token(self, city: str) -> str:
        normalized_city = (city or "").strip()
        if not normalized_city:
            return ""
        if normalized_city.isdigit():
            return normalized_city
        if normalized_city in AMapService._city_code_cache:
            return AMapService._city_code_cache[normalized_city]

        try:
            url = f"{self.base_url}/config/district"
            params = {
                "key": self.api_key,
                "keywords": normalized_city,
                "subdistrict": 0,
                "extensions": "base",
                "output": "json",
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "1":
                districts = data.get("districts") or []
                if districts:
                    adcode = districts[0].get("adcode") or ""
                    if adcode:
                        AMapService._city_code_cache[normalized_city] = adcode
                        return adcode
        except Exception as exc:
            logger.info("AMap district resolve failed for %s: %s", normalized_city, exc)

        AMapService._city_code_cache[normalized_city] = normalized_city
        return normalized_city

    def _dedupe(self, items: List[Dict]) -> List[Dict]:
        seen = set()
        unique_items = []
        for item in items:
            key = f"{item.get('name')}_{item.get('address')}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        return unique_items

    def _format_poi(self, poi: Dict) -> Dict:
        raw_location = poi.get("location") or ""
        if isinstance(raw_location, dict):
            lon = self._safe_float(raw_location.get("longitude") or raw_location.get("lng"))
            lat = self._safe_float(raw_location.get("latitude") or raw_location.get("lat"))
        elif isinstance(raw_location, str):
            location = raw_location.split(",")
            lon = self._safe_float(location[0] if len(location) > 0 else 0)
            lat = self._safe_float(location[1] if len(location) > 1 else 0)
        else:
            lon = 0.0
            lat = 0.0

        cost = poi.get("cost", poi.get("price", "0"))
        price = int(self._safe_float(cost))

        biz_ext = poi.get("biz_ext", {})
        rating = None
        if isinstance(biz_ext, str):
            try:
                biz_dict = json.loads(biz_ext.replace("'", '"'))
                rating = self._safe_float(biz_dict.get("rating"))
            except Exception:
                rating = None
        elif isinstance(biz_ext, dict):
            rating = self._safe_float(biz_ext.get("rating"))
        if rating in (0.0, None):
            rating = self._safe_float(poi.get("rating"))

        business_area = poi.get("business_area", poi.get("adname", ""))
        if isinstance(business_area, list):
            business_area = business_area[0] if business_area else ""

        distance = poi.get("distance", "")
        if isinstance(distance, list):
            distance = distance[0] if distance else ""

        return {
            "name": poi.get("name", ""),
            "address": poi.get("address", poi.get("formatted_address", "")),
            "location": {"longitude": lon, "latitude": lat},
            "typecode": poi.get("typecode", poi.get("type", "")),
            "tel": poi.get("tel", ""),
            "price": price,
            "rating": rating,
            "business_area": business_area,
            "distance": distance,
        }

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0
