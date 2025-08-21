from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from app.models.common import GeoPoint

WasteType = Literal[
    "organic",
    "recyclable_plastic",
    "recyclable_paper",
    "recyclable_glass",
    "e_waste",
    "waste_collection",
    "mixed",
]

CollectionMethod = Literal[
    "curbside",
    "door_to_door",
    "drop_off",
    "pickup_services",
    "return_system",
]

class ReportCreate(BaseModel):
    # student_id: str
    nearest_institution_id: Optional[str] = None
    image_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    measure_height_cm: Optional[float] = None
    measure_width_cm: Optional[float] = None
    waste_type: WasteType
    feedback: Optional[str] = None
    safe: bool = True
    urban_area: bool = True
    children_present: bool = False
    flood_risk: bool = False
    animals_present: bool = False
    collection_method: Optional[CollectionMethod] = None
    location: GeoPoint

class ReportPublic(ReportCreate):
    id: str = Field(alias="_id")
    status: Literal["new", "assigned", "cleared"] = "new"
    priority: int = 0