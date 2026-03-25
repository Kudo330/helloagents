from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.attraction import Attraction
from app.models.hotel import Hotel
from app.models.meal import Meal
from app.models.transport import TransportLeg


class DayPlan(BaseModel):
    """Single day travel plan."""

    date: str = Field(..., description="Date")
    day_index: int = Field(..., description="Zero-based day index")
    description: str = Field(..., description="Daily itinerary summary")
    transportation: str = Field(..., description="Transportation preference")
    accommodation: str = Field(..., description="Accommodation preference")
    hotel: Optional[Hotel] = Field(default=None, description="Hotel info")
    attractions: List[Attraction] = Field(default_factory=list, description="Attractions")
    meals: List[Meal] = Field(default_factory=list, description="Meals")
    transport_legs: List[TransportLeg] = Field(default_factory=list, description="Route legs")
