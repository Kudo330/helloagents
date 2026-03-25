"""Weather service with MCP-first lookup and REST fallback."""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from app.config import get_settings
from app.services.mcp_service import MCPToolService

logger = logging.getLogger(__name__)


class WeatherService:
    """Wrapper around AMap weather APIs."""

    _cache: Dict[str, Dict] = {}
    _city_code_cache: Dict[str, str] = {}
    _request_lock = threading.Lock()
    _last_request_ts = 0.0
    _min_request_interval = 0.35

    def __init__(self):
        self.settings = get_settings()
        self.api_key = (self.settings.amap_api_key or "").strip()
        self.base_url = "https://restapi.amap.com/v3"
        self.timeout = 3
        self.disabled = not bool(self.api_key)
        self.use_mcp = bool(self.settings.use_amap_mcp)
        self.mcp_service = MCPToolService() if self.use_mcp else None
        if self.disabled:
            logger.info("WeatherService disabled because amap_api_key is missing")

    def get_weather(self, city: str) -> Optional[Dict]:
        if self.disabled:
            return None
        normalized_city = (city or "").strip()
        if normalized_city in WeatherService._cache:
            return dict(WeatherService._cache[normalized_city])

        city_token = self._resolve_city_token(normalized_city)
        mcp_result = self._get_weather_via_mcp(city_token or normalized_city)
        if mcp_result:
            WeatherService._cache[normalized_city] = dict(mcp_result)
            return mcp_result

        rest_result = self._get_weather_via_rest(normalized_city, city_token)
        if rest_result:
            WeatherService._cache[normalized_city] = dict(rest_result)
        return rest_result

    def _get_weather_via_mcp(self, city_token: str) -> Optional[Dict]:
        if not self.mcp_service:
            return None
        try:
            result = self.mcp_service.get_weather(city_token)
            if result and result.get("casts"):
                logger.info("AMap MCP weather hit for %s", city_token)
                return result
        except Exception as exc:
            logger.info("AMap MCP weather failed for %s: %s", city_token, exc)
        return None

    def _get_weather_via_rest(self, normalized_city: str, city_token: str) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/weather/weatherInfo"
            params = {"key": self.api_key, "city": city_token, "extensions": "all"}
            with WeatherService._request_lock:
                now = time.monotonic()
                wait_seconds = WeatherService._min_request_interval - (now - WeatherService._last_request_ts)
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                response = requests.get(url, params=params, timeout=self.timeout)
                WeatherService._last_request_ts = time.monotonic()
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "1":
                forecasts = data.get("forecasts", [])
                if forecasts:
                    return {
                        "city": forecasts[0].get("city"),
                        "province": forecasts[0].get("province"),
                        "casts": forecasts[0].get("casts", []),
                    }
            logger.warning("Weather fetch failed: %s", data.get("info", "unknown error"))
            if normalized_city in WeatherService._cache:
                return dict(WeatherService._cache[normalized_city])
            return None
        except Exception as exc:
            logger.warning("Weather fetch exception: %s", exc)
            if normalized_city in WeatherService._cache:
                return dict(WeatherService._cache[normalized_city])
            return None

    def get_weather_forecast(self, city: str, start_date: str, days: int) -> List[Dict]:
        weather_data = self.get_weather(city)
        if not weather_data:
            return []

        forecasts = []
        casts = weather_data.get("casts", [])
        for index in range(min(days, len(casts))):
            cast = casts[index]
            forecasts.append(
                {
                    "date": cast.get("date"),
                    "day_weather": cast.get("dayweather"),
                    "night_weather": cast.get("nightweather"),
                    "day_temp": int(cast.get("daytemp", 0)),
                    "night_temp": int(cast.get("nighttemp", 0)),
                    "day_wind_direction": cast.get("daywind", ""),
                    "day_wind_power": cast.get("daypower", ""),
                    "night_wind_direction": cast.get("nightwind", ""),
                    "night_wind_power": cast.get("nightpower", ""),
                }
            )

        while forecasts and len(forecasts) < days:
            last = forecasts[-1]
            next_date = self._next_day(last["date"])
            forecasts.append(
                {
                    "date": next_date,
                    "day_weather": last["day_weather"],
                    "night_weather": last["night_weather"],
                    "day_temp": last["day_temp"],
                    "night_temp": last["night_temp"],
                    "day_wind_direction": last["day_wind_direction"],
                    "day_wind_power": last["day_wind_power"],
                    "night_wind_direction": last["night_wind_direction"],
                    "night_wind_power": last["night_wind_power"],
                }
            )
        return forecasts

    def _next_day(self, date_str: str) -> str:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return (date + timedelta(days=1)).strftime("%Y-%m-%d")

    def get_weather_for_dates(self, city: str, dates: List[str]) -> List[Dict]:
        if not dates:
            return []
        forecasts = self.get_weather_forecast(city, dates[0], len(dates))
        date_set = set(dates)
        return [forecast for forecast in forecasts if forecast["date"] in date_set]

    def _resolve_city_token(self, city: str) -> str:
        normalized_city = (city or "").strip()
        if not normalized_city:
            return ""
        if normalized_city.isdigit():
            return normalized_city
        if normalized_city in WeatherService._city_code_cache:
            return WeatherService._city_code_cache[normalized_city]

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
                        WeatherService._city_code_cache[normalized_city] = adcode
                        return adcode
        except Exception as exc:
            logger.info("Weather city resolve failed for %s: %s", normalized_city, exc)

        WeatherService._city_code_cache[normalized_city] = normalized_city
        return normalized_city
