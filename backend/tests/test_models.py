"""数据模型测试"""

import pytest
from app.models import (
    TripPlanRequest,
    TripPlan,
    DayPlan,
    Attraction,
    Location,
    Meal,
    Budget,
    WeatherInfo
)


class TestTripPlanRequest:
    """测试旅行计划请求模型"""

    def test_valid_trip_plan_request(self):
        """测试有效的请求"""
        request = TripPlanRequest(
            city="杭州",
            start_date="2026-03-10",
            end_date="2026-03-12",
            days=3,
            preferences="历史文化",
            budget="中等",
            transportation="公共交通",
            accommodation="经济型酒店"
        )

        assert request.city == "杭州"
        assert request.days == 3
        assert request.budget == "中等"

    def test_invalid_city_empty(self):
        """测试空城市名称"""
        with pytest.raises(ValueError):
            TripPlanRequest(
                city="",
                start_date="2026-03-10",
                end_date="2026-03-12",
                days=3
            )

    def test_invalid_days_too_large(self):
        """测试天数超过限制"""
        with pytest.raises(ValueError):
            TripPlanRequest(
                city="杭州",
                start_date="2026-03-10",
                end_date="2026-03-12",
                days=15
            )


class TestAttraction:
    """测试景点模型"""

    def test_valid_attraction(self):
        """测试有效的景点"""
        attraction = Attraction(
            name="西湖",
            address="浙江省杭州市西湖区",
            location={"longitude": 120.1, "latitude": 30.2},
            visit_duration=120,
            description="杭州最著名的景点",
            category="自然风光",
            rating=4.5,
            ticket_price=0
        )

        assert attraction.name == "西湖"
        assert attraction.ticket_price == 0
        assert attraction.location.latitude == 30.2


class TestMeal:
    """测试餐饮模型"""

    def test_valid_meal(self):
        """测试有效的餐饮"""
        meal = Meal(
            type="breakfast",
            name="杭州小笼包",
            address="浙江省杭州市",
            description="杭州特色小吃",
            estimated_cost=30
        )

        assert meal.type == "breakfast"
        assert meal.estimated_cost == 30

    def test_invalid_meal_type(self):
        """测试无效的餐饮类型"""
        with pytest.raises(ValueError):
            Meal(
                type="invalid_type",
                name="测试",
                estimated_cost=50
            )


class TestWeatherInfo:
    """测试天气信息模型"""

    def test_valid_weather(self):
        """测试有效的天气信息"""
        weather = WeatherInfo(
            date="2026-03-10",
            day_weather="晴",
            night_weather="多云",
            day_temp=20,
            night_temp=15,
            wind_direction="东南",
            wind_power="2级"
        )

        assert weather.day_temp == 20
        assert weather.night_temp == 15
        assert weather.day_weather == "晴"


class TestBudget:
    """测试预算模型"""

    def test_valid_budget(self):
        """测试有效的预算"""
        budget = Budget(
            total_attractions=200,
            total_hotels=500,
            total_meals=300,
            total_transportation=100,
            total=1100
        )

        assert budget.total == 1100
        assert budget.total_attractions == 200

    def test_budget_negative_values(self):
        """测试负值"""
        with pytest.raises(ValueError):
            Budget(
                total_attractions=-100,
                total_hotels=500,
                total_meals=300,
                total_transportation=100,
                total=800
            )

    def test_budget_total_validation(self):
        """测试总费用验证"""
        # 测试总费用不正确的情况（应该被自动修正）
        budget = Budget(
            total_attractions=200,
            total_hotels=500,
            total_meals=300,
            total_transportation=100,
            total=999  # 错误的总费用
        )

        # 应该被修正为正确的总和
        assert budget.total == 1100
