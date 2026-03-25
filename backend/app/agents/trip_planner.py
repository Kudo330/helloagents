"""Multi-agent travel planner orchestration."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.config import get_settings
from app.models import Attraction, Budget, DayPlan, Hotel, Meal, TripPlan, TripPlanRequest, WeatherInfo
from app.services.amap_service import AMapService
from app.services.route_service import RouteService
from app.services.unsplash_service import UnsplashService
from app.services.weather_service import WeatherService
from app.utils import get_logger

logger = get_logger(__name__)
BAD_WEATHER_KEYWORDS = ("雨", "雷", "雪", "暴")
INDOOR_KEYWORDS = ("博物馆", "美术馆", "艺术馆", "展览", "书店", "商场", "室内", "展馆")
DEFAULT_IMAGE_URL = "https://images.unsplash.com/photo-15422596812-9ac549a8ddd?w=800&q=80"


class BaseAgent:
    """Shared LLM wrapper used by all task agents."""

    _runtime_llm_disabled = False

    def __init__(self, client: Optional[OpenAI], model: str, name: str):
        self.client = client
        self.model = model
        self.name = name

    def call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.5,
        max_tokens: int = 1200,
    ) -> str:
        if BaseAgent._runtime_llm_disabled:
            raise RuntimeError("LLM runtime disabled after previous failure")
        if not self.client or not self.model:
            raise RuntimeError(f"{self.name} missing llm client or model")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            message = str(exc).lower()
            if any(token in message for token in ["timeout", "timed out", "insufficient_quota", "429"]):
                BaseAgent._runtime_llm_disabled = True
                logger.warning("[%s] LLM disabled for current runtime after failure: %s", self.name, exc)
            raise

    @staticmethod
    def extract_json(text: str) -> str:
        text = (text or "").strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]

        array_start = text.find("[")
        array_end = text.rfind("]")
        object_start = text.find("{")
        object_end = text.rfind("}")

        if array_start != -1 and array_end != -1 and array_start < array_end:
            return text[array_start : array_end + 1]
        if object_start != -1 and object_end != -1 and object_start < object_end:
            return text[object_start : object_end + 1]
        return text


class WeatherAgent(BaseAgent):
    def __init__(self, client: Optional[OpenAI], model: str, name: str):
        super().__init__(client, model, name)
        self.weather_service = WeatherService()

    def get_weather(self, city: str, dates: List[str]) -> List[WeatherInfo]:
        try:
            forecasts = self.weather_service.get_weather_for_dates(city, dates)
            if forecasts:
                return [
                    WeatherInfo(
                        date=item.get("date", ""),
                        day_weather=item.get("day_weather", "晴"),
                        night_weather=item.get("night_weather", "多云"),
                        day_temp=item.get("day_temp", 26),
                        night_temp=item.get("night_temp", 18),
                        wind_direction=item.get("day_wind_direction") or item.get("wind_direction", "东风"),
                        wind_power=item.get("day_wind_power") or item.get("wind_power", "3级"),
                    )
                    for item in forecasts
                ]
        except Exception as exc:
            logger.info("[%s] weather service failed: %s", self.name, exc)

        return [
            WeatherInfo(
                date=date,
                day_weather="晴",
                night_weather="多云",
                day_temp=26,
                night_temp=18,
                wind_direction="东风",
                wind_power="3级",
            )
            for date in dates
        ]


class AttractionAgent(BaseAgent):
    def __init__(self, client: Optional[OpenAI], model: str, name: str):
        super().__init__(client, model, name)
        self.amap_service = AMapService()

    def recommend_attractions(
        self,
        city: str,
        days: int,
        preferences: str,
        budget: str,
        prefer_fast: bool = False,
    ) -> Dict[int, List[Attraction]]:
        target_count = max(days * 2, 4)
        minimum_pool = max(target_count, 15)
        selected: List[Attraction] = []
        try:
            real_attractions = self.amap_service.search_attractions(city)
            selected = [self._to_attraction_model(item) for item in real_attractions[:minimum_pool]]
        except Exception as exc:
            logger.info("[%s] amap attractions failed: %s", self.name, exc)

        if len(selected) < minimum_pool and self.client:
            selected.extend(self._generate_missing_attractions(city, minimum_pool - len(selected), preferences, budget))

        if len(selected) < minimum_pool:
            selected.extend(self._fallback_attractions(city, minimum_pool - len(selected), offset=len(selected)))

        selected = self._dedupe_attractions(selected)
        selected = self._ensure_theme_variety(city, selected, minimum_pool)
        arranged = self._arrange_diverse_attractions(selected, days)

        attractions_by_day: Dict[int, List[Attraction]] = {}
        for day_index in range(days):
            start = day_index * 2
            day_items = arranged[start : start + 2]
            if len(day_items) < 2:
                day_items.extend(self._fallback_attractions(city, 2 - len(day_items), offset=day_index))
            attractions_by_day[day_index] = day_items[:2]
        return attractions_by_day

    def _generate_missing_attractions(self, city: str, count: int, preferences: str, budget: str) -> List[Attraction]:
        prompt = f"""请为{city}独自旅行补充 {count} 个景点推荐。\n偏好：{preferences}\n预算：{budget}\n请严格返回 JSON 数组，每项包含：name, address, location, visit_duration, description, category, rating, ticket_price。location 返回 {{\"longitude\": number, \"latitude\": number}}。"""
        messages = [
            {"role": "system", "content": "你是景点推荐助手，只返回 JSON。"},
            {"role": "user", "content": prompt},
        ]
        try:
            result = self.call_llm(messages, temperature=0.6, max_tokens=1000)
            data = json.loads(self.extract_json(result))
            return [self._normalize_generated_attraction(item) for item in data][:count]
        except Exception as exc:
            logger.warning("[%s] llm attraction fill failed: %s", self.name, exc)
            return []

    @staticmethod
    def _fallback_attractions(city: str, count: int, offset: int = 0) -> List[Attraction]:
        templates = [
            ("城市博物馆", "室内景点", "适合先了解城市历史与文化脉络，白天参观更从容。", 0),
            ("本地文化街区", "城市漫步", "适合独自慢逛拍照，周边餐饮更集中。", 0),
            ("人文书店", "室内景点", "适合休息和补充机动时间，雨天也较友好。", 0),
            ("城市公园", "自然景点", "适合留出轻松步行时间，整体节奏不会太赶。", 0),
            ("艺术展览馆", "室内景点", "适合在天气波动时替代部分户外安排。", 30),
            ("特色市集", "生活体验", "适合体验本地生活，晚上也相对稳妥。", 0),
        ]
        results: List[Attraction] = []
        for index in range(count):
            name, category, description, ticket_price = templates[(offset + index) % len(templates)]
            results.append(
                Attraction(
                    name=f"{city}{name}",
                    address=f"{city}中心城区",
                    location={"longitude": 114.30, "latitude": 30.59},
                    visit_duration=90,
                    description=description,
                    category=category,
                    rating=4.4,
                    ticket_price=ticket_price,
                )
            )
        return results

    @staticmethod
    def _dedupe_attractions(attractions: List[Attraction]) -> List[Attraction]:
        deduped: List[Attraction] = []
        seen: set[str] = set()
        for attraction in attractions:
            key = attraction.name.strip()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(attraction)
        return deduped

    @staticmethod
    def _theme_of_attraction(attraction: Attraction) -> str:
        name_text = attraction.name or ""
        category_text = attraction.category or ""
        text = f"{name_text}{category_text}"
        if any(keyword in name_text for keyword in ["海洋", "海底世界", "海军", "极地", "海滨", "水族", "海之恋"]):
            return "marine"
        if any(keyword in name_text for keyword in ["动物园", "动物", "熊猫", "鸟类", "野生"]):
            return "animal"
        if any(keyword in text for keyword in ["博物馆", "展览", "艺术", "美术馆", "书店", "历史", "文化"]):
            return "culture"
        if any(keyword in text for keyword in ["公园", "山", "步道", "森林", "自然", "湿地"]):
            return "nature"
        if any(keyword in text for keyword in ["广场", "街区", "市集", "地标", "老城", "商圈"]):
            return "urban"
        return "mixed"

    def _arrange_diverse_attractions(self, attractions: List[Attraction], days: int) -> List[Attraction]:
        if not attractions:
            return []

        pools: Dict[str, List[Attraction]] = {}
        for attraction in attractions:
            theme = self._theme_of_attraction(attraction)
            pools.setdefault(theme, []).append(attraction)

        arranged: List[Attraction] = []
        prev_day_themes: set[str] = set()
        used_names: set[str] = set()

        for _day_index in range(days):
            day_items: List[Attraction] = []
            day_themes: set[str] = set()

            for _slot in range(2):
                candidate = None
                candidate_theme = None

                for theme, theme_items in sorted(pools.items(), key=lambda item: len(item[1]), reverse=True):
                    if theme in day_themes:
                        continue
                    if theme in prev_day_themes and len(pools) > 2:
                        continue

                    while theme_items and theme_items[0].name in used_names:
                        theme_items.pop(0)
                    if theme_items:
                        candidate = theme_items.pop(0)
                        candidate_theme = theme
                        break

                if candidate is None:
                    for theme, theme_items in pools.items():
                        while theme_items and theme_items[0].name in used_names:
                            theme_items.pop(0)
                        if theme_items:
                            candidate = theme_items.pop(0)
                            candidate_theme = theme
                            break

                if candidate is None:
                    break

                used_names.add(candidate.name)
                day_themes.add(candidate_theme or "mixed")
                day_items.append(candidate)

            arranged.extend(day_items)
            prev_day_themes = set(day_themes)

        remaining: List[Attraction] = []
        for theme_items in pools.values():
            remaining.extend([item for item in theme_items if item.name not in used_names])
        arranged.extend(remaining)
        return arranged

    def _ensure_theme_variety(self, city: str, attractions: List[Attraction], minimum_pool: int) -> List[Attraction]:
        theme_counts: Dict[str, int] = {}
        for attraction in attractions:
            theme = self._theme_of_attraction(attraction)
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        fillers = [
            ("culture", Attraction(
                name=f"{city}城市博物馆",
                address=f"{city}中心城区",
                location={"longitude": 114.30, "latitude": 30.59},
                visit_duration=90,
                description="适合补充城市历史与文化信息，便于把每日主题拉开。",
                category="文化展馆",
                rating=4.5,
                ticket_price=0,
            )),
            ("culture", Attraction(
                name=f"{city}艺术展览馆",
                address=f"{city}中心城区",
                location={"longitude": 114.31, "latitude": 30.58},
                visit_duration=90,
                description="适合在海滨或公园类景点之间插入室内文化行程。",
                category="艺术展馆",
                rating=4.4,
                ticket_price=30,
            )),
            ("urban", Attraction(
                name=f"{city}本地文化街区",
                address=f"{city}老城片区",
                location={"longitude": 114.29, "latitude": 30.57},
                visit_duration=120,
                description="适合城市漫步、街区观察和独自打卡。",
                category="城市街区",
                rating=4.4,
                ticket_price=0,
            )),
            ("urban", Attraction(
                name=f"{city}特色市集",
                address=f"{city}核心商圈",
                location={"longitude": 114.28, "latitude": 30.56},
                visit_duration=90,
                description="适合体验本地生活和夜间轻量活动。",
                category="生活体验",
                rating=4.3,
                ticket_price=0,
            )),
        ]

        existing_names = {item.name for item in attractions}
        result = list(attractions)
        for theme, filler in fillers:
            if theme_counts.get(theme, 0) >= 2 and len(result) >= minimum_pool:
                continue
            if filler.name in existing_names:
                continue
            result.append(filler)
            existing_names.add(filler.name)
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
            if len(result) >= minimum_pool and all(theme_counts.get(key, 0) >= 1 for key in ["culture", "urban"]):
                break

        return result

    @staticmethod
    def _normalize_generated_attraction(data: Dict[str, Any]) -> Attraction:
        location = data.get("location") or {"longitude": 0, "latitude": 0}
        if isinstance(location, str):
            parts = location.split(",")
            location = {
                "longitude": float(parts[0]) if len(parts) > 0 and parts[0] else 0,
                "latitude": float(parts[1]) if len(parts) > 1 and parts[1] else 0,
            }
        visit_duration = data.get("visit_duration", 120)
        if isinstance(visit_duration, str):
            digits = "".join(ch for ch in visit_duration if ch.isdigit())
            visit_duration = int(digits) if digits else 120
        ticket_price = data.get("ticket_price", 0)
        if isinstance(ticket_price, str):
            digits = "".join(ch for ch in ticket_price if ch.isdigit())
            ticket_price = int(digits) if digits else 0
        rating = data.get("rating", 4.3)
        try:
            rating = float(rating)
        except Exception:
            rating = 4.3
        return Attraction(
            name=data.get("name", ""),
            address=data.get("address", ""),
            location=location,
            visit_duration=int(visit_duration or 120),
            description=data.get("description") or "适合独自旅行打卡",
            category=data.get("category") or "景点",
            rating=rating,
            ticket_price=int(ticket_price or 0),
        )

    @staticmethod
    def _to_attraction_model(data: Dict[str, Any]) -> Attraction:
        location = data.get("location") or {"longitude": 0, "latitude": 0}
        return Attraction(
            name=data.get("name", ""),
            address=data.get("address", ""),
            location=location,
            visit_duration=120,
            description=data.get("description") or f"位于{data.get('business_area', '市区')}，适合独自旅行打卡",
            category=data.get("category") or data.get("typecode", "景点"),
            rating=float(data.get("rating") or 4.3),
            ticket_price=int(data.get("ticket_price") or data.get("price") or 0),
        )


class HotelAgent(BaseAgent):
    def __init__(self, client: Optional[OpenAI], model: str, name: str):
        super().__init__(client, model, name)
        self.amap_service = AMapService()

    def recommend_hotel(self, city: str, accommodation: str, budget: str) -> Optional[Hotel]:
        try:
            hotels = self.amap_service.search_hotels(city, accommodation)
            if hotels:
                best = max(hotels, key=self._hotel_score)
                return self._to_hotel_model(best, accommodation, budget)
        except Exception as exc:
            logger.info("[%s] amap hotels failed: %s", self.name, exc)

        if self.client:
            prompt = f"""请为{city}的独自旅行推荐一家{accommodation}，预算等级为{budget}。请严格返回 JSON，对象字段包含：name, address, location, price_range, rating, distance, type, estimated_cost。"""
            messages = [
                {"role": "system", "content": "你是酒店推荐助手，只返回 JSON。"},
                {"role": "user", "content": prompt},
            ]
            try:
                result = self.call_llm(messages, max_tokens=400)
                data = json.loads(self.extract_json(result))
                return Hotel(**data)
            except Exception as exc:
                logger.warning("[%s] llm hotel failed: %s", self.name, exc)

        return self._fallback_hotel(city, accommodation, budget)

    @staticmethod
    def _fallback_hotel(city: str, accommodation: str, budget: str) -> Hotel:
        estimated_cost = {"经济": 220, "中等": 420, "豪华": 880}.get(budget, 420)
        return Hotel(
            name=f"{city}{accommodation}",
            address=f"{city}中心城区",
            location={"longitude": 114.30, "latitude": 30.59},
            price_range=f"{max(estimated_cost - 80, 0)}-{estimated_cost + 80}元/晚",
            rating="4.5",
            distance="交通便利",
            type=accommodation,
            estimated_cost=estimated_cost,
        )

    @staticmethod
    def _to_hotel_model(data: Dict[str, Any], accommodation: str, budget: str) -> Hotel:
        default_cost = {"经济": 220, "中等": 450, "豪华": 900}.get(budget, 450)
        estimated_cost = int(data.get("price") or default_cost)
        return Hotel(
            name=data.get("name", ""),
            address=data.get("address", ""),
            location=data.get("location") or {"longitude": 0, "latitude": 0},
            price_range=data.get("price_range") or f"{max(estimated_cost - 100, 0)}-{estimated_cost + 100}元/晚",
            rating=str(data.get("rating") or "4.5"),
            distance=str(data.get("distance") or "近市中心"),
            type=accommodation,
            estimated_cost=estimated_cost,
        )

    @staticmethod
    def _hotel_score(data: Dict[str, Any]) -> tuple[float, int]:
        rating = float(data.get("rating") or 0.0)
        address = str(data.get("address") or "")
        business_area = str(data.get("business_area") or "")
        text = f"{address}{business_area}"
        penalty = 0
        if any(token in text for token in ["城阳", "即墨", "胶州", "黄岛", "平度", "莱西"]):
            penalty = -2
        return (rating, penalty)


class MealAgent(BaseAgent):
    def __init__(self, client: Optional[OpenAI], model: str, name: str):
        super().__init__(client, model, name)
        self.amap_service = AMapService()

    def recommend_meals(self, city: str, days: int, budget: str) -> Dict[int, List[Meal]]:
        meals_by_day: Dict[int, List[Meal]] = {}
        restaurant_types = "050100|050200|050300|050400|050500|050600|050700|050800|050900"
        all_restaurants: List[Dict[str, Any]] = []
        try:
            all_restaurants = self.amap_service.search_restaurants(city)
        except Exception as exc:
            logger.info("[%s] amap meals failed: %s", self.name, exc)

        meal_types = [("breakfast", "早餐", 30), ("lunch", "午餐", 50), ("dinner", "晚餐", 80)]
        multiplier = {"经济": 0.8, "中等": 1.0, "豪华": 1.5}.get(budget, 1.0)
        keyword_groups = {
            "breakfast": ["早餐", "早点", "早茶", "咖啡"],
            "lunch": ["午餐", "家常菜", "面馆", "小馆"],
            "dinner": ["晚餐", "海鲜", "大排档", "特色菜"],
        }
        meal_candidates: Dict[str, List[Dict[str, Any]]] = {key: [] for key, _, _ in meal_types}
        seen_meal_names: set[str] = set()

        for meal_key, _, _ in meal_types:
            for keyword in keyword_groups[meal_key]:
                try:
                    meal_candidates[meal_key].extend(self.amap_service.search_poi(keyword, city, restaurant_types))
                except Exception as exc:
                    logger.info("[%s] amap %s search failed: %s", self.name, meal_key, exc)
                if len(meal_candidates[meal_key]) >= 6:
                    break
            if all_restaurants:
                meal_candidates[meal_key].extend(all_restaurants)
            meal_candidates[meal_key] = self._dedupe_restaurants(meal_candidates[meal_key])

        for day_index in range(days):
            day_meals: List[Meal] = []
            for meal_offset, (meal_type, meal_label, base_cost) in enumerate(meal_types):
                estimated_cost = int(base_cost * multiplier)
                candidates = meal_candidates.get(meal_type) or []
                restaurant = self._pick_unique_restaurant(candidates, seen_meal_names)
                if restaurant:
                    business_area = restaurant.get("business_area")
                    if isinstance(business_area, list):
                        business_area = business_area[0] if business_area else "市区"
                    if not business_area:
                        business_area = "市区"
                    restaurant_name = restaurant.get("name", "")
                    if restaurant_name:
                        seen_meal_names.add(self._normalize_restaurant_name(restaurant_name))
                    day_meals.append(
                        Meal(
                            type=meal_type,
                            name=f"{meal_label}: {restaurant_name}",
                            address=restaurant.get("address", ""),
                            location=restaurant.get("location"),
                            description=f"位于{business_area}，适合独自旅行就餐",
                            estimated_cost=estimated_cost,
                        )
                    )
                else:
                    fallback_meal = self._build_fallback_meal(city, meal_type, meal_label, estimated_cost, day_index)
                    seen_meal_names.add(self._normalize_restaurant_name(fallback_meal.name))
                    day_meals.append(fallback_meal)
            meals_by_day[day_index] = day_meals
        return meals_by_day

    @staticmethod
    def _dedupe_restaurants(restaurants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in restaurants:
            key = f"{item.get('name', '')}|{item.get('address', '')}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    @staticmethod
    def _pick_unique_restaurant(candidates: List[Dict[str, Any]], seen_names: set[str]) -> Optional[Dict[str, Any]]:
        if not candidates:
            return None
        for restaurant in candidates:
            name = restaurant.get("name", "")
            normalized_name = MealAgent._normalize_restaurant_name(name)
            if name and normalized_name not in seen_names:
                return restaurant
        return None

    @staticmethod
    def _normalize_restaurant_name(name: str) -> str:
        if not name:
            return ""
        normalized = name.strip()
        if "·" in normalized:
            normalized = normalized.split("·", 1)[0]
        if "(" in normalized:
            normalized = normalized.split("(", 1)[0]
        if "（" in normalized:
            normalized = normalized.split("（", 1)[0]
        for suffix in ["店", "旗舰", "海鲜", "烧烤", "大排档"]:
            if normalized.endswith(suffix) and len(normalized) > len(suffix) + 1:
                normalized = normalized[:-len(suffix)]
        return normalized.strip()

    @staticmethod
    def _build_fallback_meal(city: str, meal_type: str, meal_label: str, estimated_cost: int, day_index: int) -> Meal:
        templates = {
            "breakfast": ["酒店早餐", "社区早点铺", "本地面馆", "老字号包子铺", "街角豆浆店", "晨间咖啡馆"],
            "lunch": ["口碑家常菜馆", "本地特色小馆", "商圈简餐店", "海鲜盖饭店", "老城饺子馆", "人气砂锅店"],
            "dinner": ["热门晚餐餐厅", "夜市美食档口", "评价稳定的餐馆", "本地海鲜馆", "港风小馆", "晚间烧烤店"],
        }
        options = templates.get(meal_type, [meal_label])
        name = f"{city}{options[day_index % len(options)]}{day_index + 1}号店"
        return Meal(
            type=meal_type,
            name=f"{meal_label}: {name}",
            address=f"{city}中心城区",
            description="在缺少实时餐饮数据时提供的稳妥就餐备选，适合独自旅行。",
            estimated_cost=estimated_cost,
        )


class PlannerAgent(BaseAgent):
    def plan_daily_itineraries(
        self,
        city: str,
        day_payloads: List[Dict[str, Any]],
        transportation: str,
        accommodation: str,
        pace_preference: str,
        safety_preference: str,
        night_preference: str,
    ) -> List[str]:
        if not self.client:
            return [self._fallback_day_description(payload, transportation, safety_preference, night_preference) for payload in day_payloads]

        prompt = (
            f"请为{city}独自旅行生成 {len(day_payloads)} 天的每日行程描述。"
            f"交通方式：{transportation}；住宿安排：{accommodation}；"
            f"行程节奏：{pace_preference}；安全偏好：{safety_preference}；夜间安排：{night_preference}。"
            "请严格返回 JSON 数组，每项包含 day_index 和 description，description 控制在 90-140 字，需体现天气、安全、返程和节奏建议。"
            f"每日信息：{json.dumps(day_payloads, ensure_ascii=False)}"
        )
        messages = [
            {"role": "system", "content": "你是独自旅行行程规划助手，只返回 JSON。"},
            {"role": "user", "content": prompt},
        ]
        try:
            result = self.call_llm(messages, temperature=0.6, max_tokens=1400)
            data = json.loads(self.extract_json(result))
            description_by_index = {int(item.get("day_index", 0)): str(item.get("description", "")).strip() for item in data}
            return [
                description_by_index.get(index) or self._fallback_day_description(payload, transportation, safety_preference, night_preference)
                for index, payload in enumerate(day_payloads)
            ]
        except Exception as exc:
            logger.warning("[%s] bulk itinerary failed: %s", self.name, exc)
            return [self._fallback_day_description(payload, transportation, safety_preference, night_preference) for payload in day_payloads]

    def generate_suggestions(
        self,
        city: str,
        days: int,
        preferences: str,
        budget: str,
        pace_preference: str,
        safety_preference: str,
        night_preference: str,
        weather_overview: str,
    ) -> str:
        if not self.client:
            return self._fallback_suggestions(city, days, pace_preference, safety_preference, night_preference, weather_overview)

        prompt = f"""请为{city}{days}天独自旅行生成总体建议。
偏好：{preferences}
预算：{budget}
行程节奏：{pace_preference}
安全偏好：{safety_preference}
夜间安排：{night_preference}
天气概览：{weather_overview}
请用 3-4 句中文，覆盖节奏、安全提醒和夜间安排；如有降雨或天气波动，请补充调整建议。只返回正文。"""
        messages = [
            {"role": "system", "content": "你是独自旅行规划专家。"},
            {"role": "user", "content": prompt},
        ]
        try:
            return self.call_llm(messages, temperature=0.7, max_tokens=320).strip()
        except Exception as exc:
            logger.warning("[%s] generate suggestions failed: %s", self.name, exc)
            return self._fallback_suggestions(city, days, pace_preference, safety_preference, night_preference, weather_overview)

    def calculate_budget(
        self,
        days: int,
        attractions_by_day: Dict[int, List[Attraction]],
        meals_by_day: Dict[int, List[Meal]],
        hotel: Optional[Hotel],
        transportation: str,
    ) -> Budget:
        total_attractions = sum(sum(item.ticket_price or 0 for item in items) for items in attractions_by_day.values())
        total_meals = sum(sum(item.estimated_cost or 0 for item in items) for items in meals_by_day.values())
        total_hotels = (hotel.estimated_cost or 0) * days if hotel else 0
        total_transportation = {"公共交通": 50 * days, "打车": 200 * days, "自驾": 120 * days}.get(transportation, 100 * days)
        return Budget(
            total_attractions=total_attractions,
            total_hotels=total_hotels,
            total_meals=total_meals,
            total_transportation=total_transportation,
            total=total_attractions + total_hotels + total_meals + total_transportation,
        )

    @staticmethod
    def _fallback_day_description(payload: Dict[str, Any], transportation: str, safety_preference: str, night_preference: str) -> str:
        attraction_names = "、".join(payload.get("attractions", [])[:2]) or "城市漫步"
        meal_names = "、".join(payload.get("meals", [])[:2]) or "本地餐饮"
        weather_summary = payload.get("weather_summary", "天气平稳")
        night_hint = "建议夜间尽量在住宿点附近活动。" if safety_preference == "稳妥优先" else "夜间活动尽量控制在可快速返程的范围内。"
        if night_preference == "早归休息":
            night_hint = "晚间安排以轻松收尾和提前返程为主。"
        return f"第{payload.get('day_index', 0) + 1}天可围绕{attraction_names}展开，天气为{weather_summary}。建议搭配{meal_names}，全程以{transportation}衔接，并预留机动时间。{night_hint}"

    @staticmethod
    def _fallback_suggestions(city: str, days: int, pace_preference: str, safety_preference: str, night_preference: str, weather_overview: str) -> str:
        return (
            f"这次{city}{days}天独自旅行建议以{pace_preference}节奏推进，优先保证路线连续和返程稳定。"
            f"安全方面以{safety_preference}为原则，夜间安排建议采用“{night_preference}”策略。"
            f"天气方面可参考：{weather_overview}，遇到波动时优先调整为室内或住宿点附近行程。"
        )


class TripPlannerAgent:
    """Coordinates the end-to-end trip planning workflow."""

    def __init__(self):
        settings = get_settings()
        self.model = settings.llm_model or "MiniMax-M2.5"
        self.client: Optional[OpenAI] = None
        if settings.llm_api_key:
            self.client = OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url or None,
                timeout=8.0,
                max_retries=0,
            )
        self.unsplash_service = UnsplashService(settings.unsplash_access_key)
        self.route_service = RouteService()
        self.weather_agent = WeatherAgent(self.client, self.model, "WeatherAgent")
        self.attraction_agent = AttractionAgent(self.client, self.model, "AttractionAgent")
        self.hotel_agent = HotelAgent(self.client, self.model, "HotelAgent")
        self.meal_agent = MealAgent(self.client, self.model, "MealAgent")
        self.planner_agent = PlannerAgent(self.client, self.model, "PlannerAgent")

    def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        return self._plan_trip_impl(request, force_fast_mode=False)

    def plan_trip_quick(self, request: TripPlanRequest) -> TripPlan:
        return self._plan_trip_impl(request, force_fast_mode=True)

    def _plan_trip_impl(self, request: TripPlanRequest, force_fast_mode: bool = False) -> TripPlan:
        logger.info("Start planning %s for %s days", request.city, request.days)
        fast_mode = force_fast_mode or request.days >= 4
        dates = self._get_dates(request.start_date, request.days)
        solo_preferences = (
            f"{request.preferences}; 行程节奏:{request.pace_preference}; "
            f"安全偏好:{request.safety_preference}; 夜间安排:{request.night_preference}"
        )

        with ThreadPoolExecutor(max_workers=4) as executor:
            weather_future = executor.submit(self.weather_agent.get_weather, request.city, dates)
            attractions_future = executor.submit(
                self.attraction_agent.recommend_attractions,
                request.city,
                request.days,
                solo_preferences,
                request.budget,
                fast_mode,
            )
            hotel_future = executor.submit(self.hotel_agent.recommend_hotel, request.city, request.accommodation, request.budget)
            meals_future = executor.submit(self.meal_agent.recommend_meals, request.city, request.days, request.budget)

            weather_info = weather_future.result()
            attractions_by_day = attractions_future.result()
            hotel = hotel_future.result()
            meals_by_day = meals_future.result()

        weather_by_date = {item.date: item for item in weather_info}
        attractions_by_day = self._adapt_attractions_to_weather(request.city, dates, attractions_by_day, weather_by_date)

        day_payloads: List[Dict[str, Any]] = []
        for day_index, date in enumerate(dates):
            attractions = attractions_by_day.get(day_index, [])
            meals = meals_by_day.get(day_index, [])
            day_payloads.append(
                {
                    "day_index": day_index,
                    "date": date,
                    "weather_summary": self._weather_summary(weather_by_date.get(date)),
                    "attractions": [item.name for item in attractions],
                    "meals": [item.name for item in meals],
                }
            )

        if fast_mode:
            descriptions = [
                self.planner_agent._fallback_day_description(payload, request.transportation, request.safety_preference, request.night_preference)
                for payload in day_payloads
            ]
        else:
            descriptions = self.planner_agent.plan_daily_itineraries(
                request.city,
                day_payloads,
                request.transportation,
                request.accommodation,
                request.pace_preference,
                request.safety_preference,
                request.night_preference,
            )

        day_plans: List[DayPlan] = []
        for day_index, date in enumerate(dates):
            attractions_for_day = attractions_by_day.get(day_index, [])
            transport_legs = []
            if not fast_mode:
                transport_legs = self.route_service.build_day_legs(
                    request.city,
                    request.transportation,
                    hotel.name if hotel else None,
                    hotel.location if hotel else None,
                    [(item.name, item.location) for item in attractions_for_day],
                )
            day_plans.append(
                DayPlan(
                    date=date,
                    day_index=day_index,
                    description=descriptions[day_index],
                    transportation=request.transportation,
                    accommodation=request.accommodation,
                    hotel=hotel,
                    attractions=attractions_for_day,
                    meals=meals_by_day.get(day_index, []),
                    transport_legs=transport_legs,
                )
            )

        weather_overview = "；".join(
            self._weather_summary(weather_by_date.get(date), include_date=True) for date in dates if weather_by_date.get(date)
        ) or "天气以晴到多云为主"
        if fast_mode:
            suggestions = self.planner_agent._fallback_suggestions(
                request.city,
                request.days,
                request.pace_preference,
                request.safety_preference,
                request.night_preference,
                weather_overview,
            )
        else:
            suggestions = self.planner_agent.generate_suggestions(
                request.city,
                request.days,
                request.preferences,
                request.budget,
                request.pace_preference,
                request.safety_preference,
                request.night_preference,
                weather_overview,
            )
        budget = self.planner_agent.calculate_budget(request.days, attractions_by_day, meals_by_day, hotel, request.transportation)

        trip_plan = TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            pace_preference=request.pace_preference,
            safety_preference=request.safety_preference,
            night_preference=request.night_preference,
            solo_reminders=self._build_solo_reminders(request, weather_info),
            days=day_plans,
            weather_info=weather_info,
            overall_suggestions=suggestions,
            budget=budget,
        )
        if fast_mode:
            return trip_plan
        return self._enrich_with_images(trip_plan)

    @staticmethod
    def _get_dates(start_date: str, days: int) -> List[str]:
        current = datetime.strptime(start_date, "%Y-%m-%d")
        dates: List[str] = []
        for _ in range(days):
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        return dates

    @staticmethod
    def _weather_summary(weather: Optional[WeatherInfo], include_date: bool = False) -> str:
        if not weather:
            return "天气平稳"
        summary = f"{weather.day_weather} {weather.day_temp}℃ / {weather.night_weather} {weather.night_temp}℃"
        return f"{weather.date} {summary}" if include_date else summary

    @staticmethod
    def _is_bad_weather(weather: Optional[WeatherInfo]) -> bool:
        if not weather:
            return False
        combined = f"{weather.day_weather}{weather.night_weather}"
        return any(keyword in combined for keyword in BAD_WEATHER_KEYWORDS)

    @staticmethod
    def _is_indoor_attraction(attraction: Attraction) -> bool:
        text = f"{attraction.name}{attraction.category or ''}{attraction.description}"
        return any(keyword in text for keyword in INDOOR_KEYWORDS)

    def _adapt_attractions_to_weather(
        self,
        city: str,
        dates: List[str],
        attractions_by_day: Dict[int, List[Attraction]],
        weather_by_date: Dict[str, WeatherInfo],
    ) -> Dict[int, List[Attraction]]:
        adjusted: Dict[int, List[Attraction]] = {}
        for day_index, date in enumerate(dates):
            attractions = list(attractions_by_day.get(day_index, []))
            weather = weather_by_date.get(date)
            if not self._is_bad_weather(weather):
                adjusted[day_index] = attractions
                continue

            indoor = [item for item in attractions if self._is_indoor_attraction(item)]
            outdoor = [item for item in attractions if not self._is_indoor_attraction(item)]
            reordered = indoor + outdoor
            if not indoor:
                reordered = reordered[:1]
                reordered.append(self._build_indoor_backup(city, day_index))
            adjusted[day_index] = reordered[:2]
        return adjusted

    @staticmethod
    def _build_indoor_backup(city: str, day_index: int) -> Attraction:
        templates = ["城市博物馆", "艺术展览馆", "人文书店", "室内市集"]
        name = f"{city}{templates[day_index % len(templates)]}"
        return Attraction(
            name=name,
            address=f"{city}中心城区",
            location={"longitude": 120.15, "latitude": 30.28},
            visit_duration=90,
            description="遇到天气波动时的室内备选点，适合独自旅行临时调整。",
            category="室内景点",
            rating=4.4,
            ticket_price=0,
        )

    def _build_solo_reminders(self, request: TripPlanRequest, weather_info: List[WeatherInfo]) -> List[str]:
        reminders = [
            "出门前建议保存酒店地址、返程路线和紧急联系人信息。",
            "尽量选择交通便利、有人流的区域活动，减少临时跨区移动。",
        ]
        if any(self._is_bad_weather(item) for item in weather_info):
            reminders.append("天气有波动时，优先安排室内景点，并提前准备雨具和备用返程方案。")
        if request.safety_preference == "稳妥优先":
            reminders.append("若安排夜间活动，建议在 21:00 前回到住宿点附近区域。")
        elif request.night_preference == "夜生活体验":
            reminders.append("夜生活体验建议控制在住宿点 30 分钟返程范围内，返程尽量使用确定性更高的交通方式。")
        else:
            reminders.append("夜间活动结束后尽量避免临时换点，优先按原路线返程。")
        if request.pace_preference == "紧凑":
            reminders.append("紧凑行程建议每天预留一段机动时间，用于休息或天气变化调整。")
        return reminders[:4]

    def _enrich_with_images(self, trip_plan: TripPlan) -> TripPlan:
        if self.unsplash_service.disabled:
            for day in trip_plan.days:
                for attraction in day.attractions:
                    if not attraction.image_url:
                        attraction.image_url = DEFAULT_IMAGE_URL
            return trip_plan

        queries: List[str] = []
        seen = set()
        for day in trip_plan.days:
            for attraction in day.attractions:
                if attraction.name not in seen:
                    queries.append(attraction.name)
                    seen.add(attraction.name)
                if len(queries) >= 2:
                    break
            if len(queries) >= 2:
                break

        image_map: Dict[str, str] = {}
        for query in queries:
            image_map[query] = self.unsplash_service.get_photo_url(query) or DEFAULT_IMAGE_URL

        for day in trip_plan.days:
            for attraction in day.attractions:
                attraction.image_url = image_map.get(attraction.name, DEFAULT_IMAGE_URL)
        return trip_plan
