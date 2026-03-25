from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.budget import Budget
from app.models.day_plan import DayPlan
from app.models.weather import WeatherInfo


class TripPlanRequest(BaseModel):
    """Trip-plan input payload."""

    city: str = Field(..., description="Destination city")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")
    days: int = Field(..., description="Trip length in days", gt=0, le=14)
    preferences: str = Field(default="history,culture", description="Travel preferences")
    budget: str = Field(default="medium", description="Budget level")
    transportation: str = Field(default="public", description="Transportation type")
    accommodation: str = Field(default="economy", description="Accommodation type")
    pace_preference: str = Field(default="平衡", description="Travel pace preference")
    safety_preference: str = Field(default="稳妥优先", description="Solo travel safety preference")
    night_preference: str = Field(default="早归休息", description="Night activity preference")

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        city = value.strip()
        if not city:
            raise ValueError("city must not be empty")
        return city


class TripPlan(BaseModel):
    """Generated trip plan."""

    city: str = Field(..., description="Destination city")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    pace_preference: str = Field(default="平衡", description="Travel pace preference")
    safety_preference: str = Field(default="稳妥优先", description="Solo travel safety preference")
    night_preference: str = Field(default="早归休息", description="Night activity preference")
    solo_reminders: List[str] = Field(default_factory=list, description="Solo travel reminders")
    days: List[DayPlan] = Field(default_factory=list, description="Daily plans")
    weather_info: List[WeatherInfo] = Field(default_factory=list, description="Weather info")
    overall_suggestions: str = Field(..., description="Overall suggestions")
    budget: Optional[Budget] = Field(default=None, description="Budget summary")
