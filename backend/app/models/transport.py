from typing import Optional

from pydantic import BaseModel, Field


class TransportLeg(BaseModel):
    """Single transport segment within a day plan."""

    mode: str = Field(..., description="Transport mode")
    from_name: str = Field(..., description="Start point name")
    to_name: str = Field(..., description="End point name")
    distance_meters: int = Field(default=0, description="Distance in meters", ge=0)
    duration_minutes: int = Field(default=0, description="Duration in minutes", ge=0)
    estimated_cost: Optional[float] = Field(default=None, description="Estimated cost")
    summary: str = Field(default="", description="Human readable route summary")
