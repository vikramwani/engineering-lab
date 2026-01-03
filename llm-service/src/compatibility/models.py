"""Pydantic models for product compatibility evaluation.

This module defines the data models used for compatibility evaluation requests
and responses, including product definitions, relationship types, and validation
constraints for the compatibility service API.
"""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field


CompatibilityRelationship = Literal[
    "replacement_filter",
    "replacement_part",
    "accessory",
    "consumable",
    "power_supply",
    "not_compatible",
    "insufficient_information",
]


class Product(BaseModel):
    """Product model with structured attributes."""

    id: str
    title: str
    category: str
    brand: str
    attributes: Dict[str, object] = Field(default_factory=dict)


class CompatibilityRequest(BaseModel):
    """Request model for compatibility evaluation."""

    product_a: Product
    product_b: Product


class CompatibilityResponse(BaseModel):
    """Response model for compatibility evaluation."""

    compatible: bool
    relationship: CompatibilityRelationship
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    evidence: List[str]
