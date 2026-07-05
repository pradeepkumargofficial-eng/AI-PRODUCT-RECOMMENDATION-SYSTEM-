"""Pydantic schemas shared across the API layer."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class UserPreferences(BaseModel):
    """Payload submitted by the onboarding / preference collection flow."""
    user_id: Optional[int] = Field(
        default=None, description="Existing synthetic user id, if simulating a returning user")
    categories: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    budget: str = Field(default="medium", description="'low' | 'medium' | 'high'")
    brands: List[str] = Field(default_factory=list)
    min_rating: float = Field(default=3.5, ge=0, le=5)
    goal: str = Field(default="explore", description="e.g. 'gift', 'upgrade', 'explore', 'restock'")


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str
    description: str
    price: float
    rating: float
    num_reviews: int
    tags: List[str]
    in_stock: bool
    popularity_score: float
    image_seed: int


class RecommendationOut(ProductOut):
    match_score: int
    explanation: str
    score_breakdown: Dict[str, Any]


class RecommendationRequest(BaseModel):
    preferences: UserPreferences
    top_n: int = Field(default=12, ge=1, le=50)


class FilterQuery(BaseModel):
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    in_stock_only: bool = False
    sort_by: Optional[str] = Field(default=None, description="'price' | 'rating' | 'popularity'")
