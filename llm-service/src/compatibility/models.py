from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    replacement_filter = "replacement_filter"
    replacement_part = "replacement_part"
    accessory = "accessory"
    consumable = "consumable"
    power_supply = "power_supply"
    not_compatible = "not_compatible"
    insufficient_information = "insufficient_information"


class CompatibilityRequest(BaseModel):
    product_a: str
    product_b: str


class CompatibilityResponse(BaseModel):
    compatible: bool
    relationship: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    evidence: List[str]
