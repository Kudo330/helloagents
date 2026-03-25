from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.location import Location

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class Meal(BaseModel):
    """Meal item in a day plan."""

    type: MealType = Field(..., description="Meal type")
    name: str = Field(..., description="Meal/place name")
    address: Optional[str] = Field(default=None, description="Address")
    location: Optional[Location] = Field(default=None, description="Geo location")
    description: Optional[str] = Field(default=None, description="Description")
    estimated_cost: int = Field(default=0, description="Estimated cost")
