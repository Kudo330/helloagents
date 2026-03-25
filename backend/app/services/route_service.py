"""Route service for real transport legs based on AMap direction APIs."""

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

import requests

from app.config import get_settings
from app.models import Location, TransportLeg

logger = logging.getLogger(__name__)


class RouteService:
    """Wrapper around AMap route APIs with lightweight cache/throttling."""

    _cache: Dict[str, TransportLeg] = {}
    _request_lock = threading.Lock()
    _last_request_ts = 0.0
    _min_request_interval = 0.35

    def __init__(self):
        settings = get_settings()
        self.api_key = (settings.amap_api_key or "").strip()
        self.base_url = "https://restapi.amap.com/v3/direction"
        self.timeout = 3
        self.disabled = not bool(self.api_key)
        if self.disabled:
            logger.info("RouteService disabled because amap_api_key is missing")

    def build_day_legs(
        self,
        city: str,
        transportation: str,
        hotel_name: Optional[str],
        hotel_location: Optional[Location],
        attractions: List[Tuple[str, Location]],
    ) -> List[TransportLeg]:
        points: List[Tuple[str, Optional[Location]]] = []
        if hotel_name and hotel_location:
            points.append((hotel_name, hotel_location))
        points.extend(attractions)
        if hotel_name and hotel_location:
            points.append((hotel_name, hotel_location))

        if len(points) < 2:
            return []

        legs: List[TransportLeg] = []
        for index in range(len(points) - 1):
            from_name, from_loc = points[index]
            to_name, to_loc = points[index + 1]
            if not from_loc or not to_loc:
                continue
            leg = self.get_route_leg(city, transportation, from_name, from_loc, to_name, to_loc)
            if leg:
                legs.append(leg)
        return legs

    def get_route_leg(
        self,
        city: str,
        transportation: str,
        from_name: str,
        from_location: Location,
        to_name: str,
        to_location: Location,
    ) -> Optional[TransportLeg]:
        if self.disabled:
            return self._fallback_leg(transportation, from_name, from_location, to_name, to_location)

        origin = f"{from_location.longitude},{from_location.latitude}"
        destination = f"{to_location.longitude},{to_location.latitude}"
        cache_key = f"{transportation}|{city}|{origin}|{destination}"
        if cache_key in RouteService._cache:
            cached = RouteService._cache[cache_key]
            return cached.model_copy(update={"from_name": from_name, "to_name": to_name})

        try:
            if transportation == "公共交通":
                leg = self._fetch_transit(city, origin, destination, from_name, to_name)
            else:
                leg = self._fetch_driving(origin, destination, from_name, to_name, transportation)

            if leg:
                RouteService._cache[cache_key] = leg
                return leg
        except Exception as exc:
            logger.warning("RouteService failed for %s -> %s: %s", from_name, to_name, exc)
            self.disabled = "CUQPS" in str(exc) or self.disabled

        return self._fallback_leg(transportation, from_name, from_location, to_name, to_location)

    def _fetch_transit(self, city: str, origin: str, destination: str, from_name: str, to_name: str) -> Optional[TransportLeg]:
        url = f"{self.base_url}/transit/integrated"
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
            "city": city,
            "cityd": city,
            "extensions": "base",
            "strategy": 0,
            "nightflag": 1,
        }
        data = self._request_json(url, params)
        if data.get("status") != "1":
            raise RuntimeError(data.get("info", "transit route failed"))

        route = (data.get("route") or {}).get("transits") or []
        if not route:
            return None

        best = route[0]
        segments = best.get("segments") or []
        parts: List[str] = []
        for segment in segments[:3]:
            walking = segment.get("walking") or {}
            if walking.get("distance") and int(walking.get("distance", 0)) > 0:
                parts.append(f"步行约{max(1, int(walking.get('distance', 0)) // 80)}分钟")
            bus = segment.get("bus") or {}
            buslines = bus.get("buslines") or []
            if buslines:
                parts.append(buslines[0].get("name", "公交换乘"))

        return TransportLeg(
            mode="公共交通",
            from_name=from_name,
            to_name=to_name,
            distance_meters=int(float(best.get("distance", 0) or 0)),
            duration_minutes=max(1, int(float(best.get("duration", 0) or 0) / 60)),
            estimated_cost=float(best.get("cost", 0) or 0),
            summary=" / ".join(parts) if parts else "公交换乘",
        )

    def _fetch_driving(self, origin: str, destination: str, from_name: str, to_name: str, transportation: str) -> Optional[TransportLeg]:
        url = f"{self.base_url}/driving"
        params = {"key": self.api_key, "origin": origin, "destination": destination, "extensions": "base", "strategy": 0}
        data = self._request_json(url, params)
        if data.get("status") != "1":
            raise RuntimeError(data.get("info", "driving route failed"))

        paths = (data.get("route") or {}).get("paths") or []
        if not paths:
            return None

        best = paths[0]
        taxi_cost = data.get("route", {}).get("taxi_cost")
        mode = "打车" if transportation == "打车" else "自驾"
        return TransportLeg(
            mode=mode,
            from_name=from_name,
            to_name=to_name,
            distance_meters=int(float(best.get("distance", 0) or 0)),
            duration_minutes=max(1, int(float(best.get("duration", 0) or 0) / 60)),
            estimated_cost=float(taxi_cost) if taxi_cost not in (None, "") else None,
            summary="驾车直达",
        )

    def _request_json(self, url: str, params: Dict[str, object]) -> Dict:
        with RouteService._request_lock:
            now = time.monotonic()
            wait_seconds = RouteService._min_request_interval - (now - RouteService._last_request_ts)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            response = requests.get(url, params=params, timeout=self.timeout)
            RouteService._last_request_ts = time.monotonic()

        response.raise_for_status()
        return response.json()

    @staticmethod
    def _fallback_leg(
        transportation: str,
        from_name: str,
        from_location: Location,
        to_name: str,
        to_location: Location,
    ) -> TransportLeg:
        approx_distance = RouteService._distance_meters(from_location, to_location)
        speed = {"公共交通": 22, "打车": 28, "自驾": 30}.get(transportation, 22)
        duration_minutes = max(8, int(approx_distance / 1000 / speed * 60))
        estimated_cost = None
        summary = "按当前交通偏好估算"
        if transportation == "公共交通":
            estimated_cost = round(max(2.0, approx_distance / 5000 * 2), 1)
            summary = "公交/地铁估算"
        elif transportation == "打车":
            estimated_cost = round(max(10.0, 10 + approx_distance / 1000 * 2.4), 1)
            summary = "打车估算"
        elif transportation == "自驾":
            estimated_cost = round(max(5.0, approx_distance / 1000 * 0.9), 1)
            summary = "自驾估算"

        return TransportLeg(
            mode=transportation,
            from_name=from_name,
            to_name=to_name,
            distance_meters=approx_distance,
            duration_minutes=duration_minutes,
            estimated_cost=estimated_cost,
            summary=summary,
        )

    @staticmethod
    def _distance_meters(a: Location, b: Location) -> int:
        dx = (a.longitude - b.longitude) * 111000
        dy = (a.latitude - b.latitude) * 111000
        return int((dx * dx + dy * dy) ** 0.5)
