"""Trip planning API routes."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models import Attraction, Budget, DayPlan, Hotel, Meal, TripPlan, TripPlanRequest, WeatherInfo
from app.models.error import ConfigurationError, ErrorResponse, ExternalAPIError, ValidationError
from app.utils import get_logger

router = APIRouter()
logger = get_logger(__name__)

trip_planner_agent = None
PACE_OPTIONS = {"轻松", "平衡", "紧凑"}
SAFETY_OPTIONS = {"稳妥优先", "常规即可", "愿意夜间活动"}
NIGHT_OPTIONS = {"早归休息", "适度夜游", "夜生活体验"}
PLANNER_TIMEOUT_SECONDS = 25
QUICK_PLANNER_TIMEOUT_SECONDS = 12


def get_trip_planner():
    global trip_planner_agent
    if trip_planner_agent is None:
        from app.agents.trip_planner import TripPlannerAgent

        trip_planner_agent = TripPlannerAgent()
    return trip_planner_agent


def validate_trip_request(data: Dict[str, Any]) -> TripPlanRequest:
    errors = []
    city = data.get("city", "").strip()
    if not city:
        errors.append({"field": "city", "message": "请输入目的地城市"})
    elif len(city) > 50:
        errors.append({"field": "city", "message": "城市名不能超过 50 个字符"})

    start_date = data.get("start_date")
    end_date = data.get("end_date")
    days = data.get("days", 0)
    pace_preference = data.get("pace_preference", "平衡")
    safety_preference = data.get("safety_preference", "稳妥优先")
    night_preference = data.get("night_preference", "早归休息")

    try:
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
        else:
            errors.append({"field": "start_date", "message": "请选择开始日期"})

        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
        else:
            errors.append({"field": "end_date", "message": "请选择结束日期"})

        if (
            start_date
            and end_date
            and datetime.strptime(end_date, "%Y-%m-%d") < datetime.strptime(start_date, "%Y-%m-%d")
        ):
            errors.append({"field": "end_date", "message": "结束日期不能早于开始日期"})

        if days < 1:
            errors.append({"field": "days", "message": "行程天数至少为 1 天"})
        elif days > 14:
            errors.append({"field": "days", "message": "行程天数不能超过 14 天"})
    except ValueError:
        errors.append({"field": "date", "message": "日期格式错误，应为 YYYY-MM-DD"})

    if pace_preference not in PACE_OPTIONS:
        errors.append({"field": "pace_preference", "message": "行程节奏选项无效"})
    if safety_preference not in SAFETY_OPTIONS:
        errors.append({"field": "safety_preference", "message": "安全偏好选项无效"})
    if night_preference not in NIGHT_OPTIONS:
        errors.append({"field": "night_preference", "message": "夜间安排选项无效"})

    if errors:
        raise ValidationError("请求参数校验失败")

    return TripPlanRequest(**data)


def _date_list(start_date: str, days: int) -> List[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]


def _build_solo_suggestions(request: TripPlanRequest) -> str:
    pace_tip = {
        "轻松": "每天预留更多弹性休息时间，优先安排低强度活动。",
        "平衡": "按上午景点、午后休闲、夜间轻度活动的节奏安排行程。",
        "紧凑": "尽量串联高密度景点，但仍保留独自出行的安全缓冲。",
    }
    safety_tip = {
        "稳妥优先": "优先选择交通便利、人流较多的区域，尽量在天黑前返回住宿点。",
        "常规即可": "保持常规安全意识，注意路线和返程时间。",
        "愿意夜间活动": "可适度安排夜间活动，但建议优先选择治安较好且便于返程的区域。",
    }
    night_tip = {
        "早归休息": "夜间安排以早归休息为主，减少跨区移动。",
        "适度夜游": "可安排 1 个夜景或夜市点位，兼顾体验与安全。",
        "夜生活体验": "可增加夜游和夜间餐饮体验，但建议控制返程距离。",
    }
    return "".join(
        [
            pace_tip.get(request.pace_preference, ""),
            safety_tip.get(request.safety_preference, ""),
            night_tip.get(request.night_preference, ""),
        ]
    )


def _build_solo_reminders(request: TripPlanRequest) -> List[str]:
    reminders = [
        "独自出行建议优先保存酒店地址、返程路线和紧急联系人信息。",
        "尽量选择交通便利、人流较多的活动区域，避免临时跨区移动。",
    ]
    if request.safety_preference == "稳妥优先":
        reminders.append("如行程安排到夜间，建议在 21:00 前回到住宿点附近活动。")
    elif request.night_preference == "夜生活体验":
        reminders.append("夜生活体验建议优先选择住宿点 30 分钟返程范围内的区域。")
    else:
        reminders.append("夜间活动结束后尽量使用确定性更高的返程方式，避免临时找路。")
    if request.pace_preference == "紧凑":
        reminders.append("紧凑行程下建议每天保留 1 段机动时间，用于休息或天气变化调整。")
    return reminders[:4]


def _generate_fallback_plan(request: TripPlanRequest) -> TripPlan:
    dates = _date_list(request.start_date, request.days)

    scenic_templates = [
        "城市地标广场",
        "历史文化街区",
        "博物馆",
        "城市公园",
        "夜景观景点",
        "本地美食街",
    ]

    weather_info = [
        WeatherInfo(
            date=d,
            day_weather="晴",
            night_weather="多云",
            day_temp=26,
            night_temp=18,
            wind_direction="东南风",
            wind_power="3级",
        )
        for d in dates
    ]

    hotel = Hotel(
        name=f"{request.city}中心商务酒店",
        address=f"{request.city}市中心",
        rating="4.5",
        type=request.accommodation,
        estimated_cost=380,
    )

    days_plans: List[DayPlan] = []
    total_attractions = 0
    total_meals = 0
    night_note = "晚上建议尽量选择人流较多的区域活动。"
    if request.night_preference == "早归休息":
        night_note = "晚间以早归休息为主，保留充足安全返程时间。"
    elif request.night_preference == "夜生活体验":
        night_note = "可在住宿点附近安排夜景或夜市体验，但建议控制返程距离。"

    for idx, d in enumerate(dates):
        attractions = []
        for offset in range(2):
            scenic_name = scenic_templates[(idx * 2 + offset) % len(scenic_templates)]
            ticket_price = 50 + offset * 20
            total_attractions += ticket_price
            attractions.append(
                Attraction(
                    name=f"{request.city}{scenic_name}",
                    address=f"{request.city}核心区域",
                    location={"longitude": 120.15 + offset * 0.01, "latitude": 30.25 + offset * 0.01},
                    visit_duration=120,
                    description="适合单人游览，公共交通可达",
                    category="景点",
                    rating=4.5,
                    ticket_price=ticket_price,
                )
            )

        meal_costs = [25, 55, 85]
        meal_types = ["breakfast", "lunch", "dinner"]
        meal_names = ["酒店早餐", "本地特色餐厅", "口碑晚餐餐厅"]
        meals = []
        for m_type, m_name, m_cost in zip(meal_types, meal_names, meal_costs):
            total_meals += m_cost
            meals.append(
                Meal(
                    type=m_type,
                    name=m_name,
                    description="按独自旅行场景和预算推荐",
                    estimated_cost=m_cost,
                )
            )

        day_desc = (
            f"第 {idx + 1} 天建议先游览 {attractions[0].name}，中午在本地餐厅用餐，"
            f"下午前往 {attractions[1].name}，{night_note}"
        )

        days_plans.append(
            DayPlan(
                date=d,
                day_index=idx,
                description=day_desc,
                transportation=request.transportation,
                accommodation=request.accommodation,
                hotel=hotel,
                attractions=attractions,
                meals=meals,
            )
        )

    total_hotels = hotel.estimated_cost * request.days
    total_transportation = 80 * request.days
    total = total_attractions + total_meals + total_hotels + total_transportation

    budget = Budget(
        total_attractions=total_attractions,
        total_hotels=total_hotels,
        total_meals=total_meals,
        total_transportation=total_transportation,
        total=total,
    )

    return TripPlan(
        city=request.city,
        start_date=request.start_date,
        end_date=request.end_date,
        pace_preference=request.pace_preference,
        safety_preference=request.safety_preference,
        night_preference=request.night_preference,
        solo_reminders=_build_solo_reminders(request),
        days=days_plans,
        weather_info=weather_info,
        overall_suggestions=_build_solo_suggestions(request),
        budget=budget,
    )


@router.get("/config")
async def get_config() -> Dict[str, str]:
    settings = get_settings()
    return {"amap_web_key": settings.amap_web_key or settings.amap_api_key}


@router.post("/plan")
async def create_trip_plan(body_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        trip_request = validate_trip_request(body_data)
        logger.info(f"[API] 开始生成行程: {trip_request.city}, {trip_request.days} 天")

        settings = get_settings()
        llm_ready = bool(settings.llm_api_key and settings.llm_model)
        use_fallback = not llm_ready
        partial_fallback = False
        trip_plan = None

        if not use_fallback:
            try:
                planner = get_trip_planner()
                trip_plan = await asyncio.wait_for(
                    asyncio.to_thread(planner.plan_trip, trip_request),
                    timeout=PLANNER_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                logger.warning(f"[API] 智能体生成超时({PLANNER_TIMEOUT_SECONDS}s)，切换到快速规划")
                try:
                    planner = get_trip_planner()
                    trip_plan = await asyncio.wait_for(
                        asyncio.to_thread(planner.plan_trip_quick, trip_request),
                        timeout=QUICK_PLANNER_TIMEOUT_SECONDS,
                    )
                    partial_fallback = True
                except Exception as quick_error:
                    logger.warning(f"[API] 快速规划失败，降级到本地方案: {quick_error}")
                    use_fallback = True
            except Exception as planner_error:
                logger.error(f"[API] 智能体生成失败，切换到快速规划: {planner_error}")
                try:
                    planner = get_trip_planner()
                    trip_plan = await asyncio.wait_for(
                        asyncio.to_thread(planner.plan_trip_quick, trip_request),
                        timeout=QUICK_PLANNER_TIMEOUT_SECONDS,
                    )
                    partial_fallback = True
                except Exception as quick_error:
                    logger.warning(f"[API] 快速规划失败，降级到本地方案: {quick_error}")
                    use_fallback = True

        if use_fallback:
            trip_plan = _generate_fallback_plan(trip_request)

        result = trip_plan.model_dump()
        result["success"] = True
        result["fallback"] = use_fallback
        result["partial_fallback"] = partial_fallback

        logger.info(
            f"[API] 行程生成完成: {len(result.get('days', []))} 天, fallback={use_fallback}, partial_fallback={partial_fallback}"
        )
        return result

    except ValidationError as e:
        response = ErrorResponse(
            error=e.message,
            code=e.code,
            details=[{"field": getattr(e, "field", None), "message": e.message}],
        )
        raise HTTPException(status_code=e.status_code, content=response.model_dump())

    except ConfigurationError as e:
        response = ErrorResponse(error=e.message, code=e.code)
        raise HTTPException(status_code=e.status_code, content=response.model_dump())

    except ExternalAPIError as e:
        response = ErrorResponse(error=e.message, code=e.code)
        raise HTTPException(status_code=e.status_code, content=response.model_dump())

    except Exception as e:
        logger.error(f"[API] 生成行程失败: {e}")
        response = ErrorResponse(error="生成行程失败，请稍后重试", code="INTERNAL_ERROR")
        raise HTTPException(status_code=500, content=response.model_dump())


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    settings = get_settings()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": bool(settings.llm_api_key),
            "amap": bool(settings.amap_api_key),
            "unsplash": bool(settings.unsplash_access_key),
        },
    }
