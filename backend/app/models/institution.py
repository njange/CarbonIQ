from pydantic import BaseModel, Field
from typing import Optional
from app.models.common import GeoPoint

class InstitutionCreate(BaseModel):
    name: str
    kind: str = Field(description="school | hospital | facility")
    location: GeoPoint

class InstitutionPublic(BaseModel):
    id: str = Field(alias="_id")
    name: str
    kind: str
    location: GeoPoint