from pydantic import BaseModel, Field
from typing import Literal, Optional

class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float] = Field(..., description="[lng, lat]")
