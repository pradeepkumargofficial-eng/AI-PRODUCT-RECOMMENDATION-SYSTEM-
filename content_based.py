"""
Content-Based Filtering
------------------------
Scores each product against a user's *stated preferences* (categories,
interests, budget, preferred brands, minimum rating) without needing any
data from other users. This is the "cold start" friendly half of the
hybrid recommender - it works even for a brand new user who just finished
onboarding.

Each signal is scored 0-1 and combined with a fixed weight vector. The
weights are intentionally explicit (not learned) so the result stays
explainable: we can always say exactly which part of a user's profile
drove a given score.
"""

from typing import List, Dict, Any

BUDGET_RANGES = {
    "low": (0, 60),
    "medium": (40, 180),
    "high": (150, 100000),
}

WEIGHTS = {
    "category": 0.30,
    "interest": 0.20,
    "budget": 0.20,
    "brand": 0.15,
    "rating": 0.15,
}


def _category_score(product: Dict[str, Any], preferred_categories: List[str]) -> float:
    return 1.0 if product["category"] in preferred_categories else 0.0


def _interest_score(product: Dict[str, Any], interests: List[str]) -> float:
    return 1.0 if product.get("interest") in interests else 0.0


def _budget_score(product: Dict[str, Any], budget: str) -> float:
    lo, hi = BUDGET_RANGES.get(budget, (0, 100000))
    price = product["price"]
    if lo <= price <= hi:
        return 1.0
    # Soft falloff instead of a hard cutoff - a product $5 outside the
    # range shouldn't score identically to one that is $500 outside it.
    distance = min(abs(price - lo), abs(price - hi))
    return max(0.0, 1.0 - distance / 200)


def _brand_score(product: Dict[str, Any], preferred_brands: List[str]) -> float:
    return 1.0 if product["brand"] in preferred_brands else 0.3


def _rating_score(product: Dict[str, Any], min_rating: float) -> float:
    if product["rating"] >= min_rating:
        # Reward ratings above the floor, capped at 1.0
        return min(1.0, 0.7 + (product["rating"] - min_rating) * 0.3)
    return max(0.0, 0.5 - (min_rating - product["rating"]) * 0.4)


def content_based_scores(products: List[Dict[str, Any]],
                          preferences: Dict[str, Any]) -> Dict[int, float]:
    """
    Returns {product_id: score} where score is in [0, 1].
    `preferences` shape:
        {
          "categories": [...], "interests": [...], "budget": "low|medium|high",
          "brands": [...], "min_rating": float
        }
    """
    scores: Dict[int, float] = {}
    for p in products:
        s = (
            WEIGHTS["category"] * _category_score(p, preferences.get("categories", [])) +
            WEIGHTS["interest"] * _interest_score(p, preferences.get("interests", [])) +
            WEIGHTS["budget"] * _budget_score(p, preferences.get("budget", "medium")) +
            WEIGHTS["brand"] * _brand_score(p, preferences.get("brands", [])) +
            WEIGHTS["rating"] * _rating_score(p, preferences.get("min_rating", 3.5))
        )
        scores[p["id"]] = round(s, 4)
    return scores


def explain_content_match(product: Dict[str, Any], preferences: Dict[str, Any]) -> List[str]:
    """Produces short human-readable reasons for a content-based match."""
    reasons = []
    if product["category"] in preferences.get("categories", []):
        reasons.append(f"Matches your interest in {product['category']}")
    if product.get("interest") in preferences.get("interests", []):
        reasons.append(f"Aligned with your '{product['interest']}' interest")
    if product["brand"] in preferences.get("brands", []):
        reasons.append(f"From {product['brand']}, one of your preferred brands")
    if product["rating"] >= preferences.get("min_rating", 3.5):
        reasons.append(f"Highly rated at {product['rating']}★")
    lo, hi = BUDGET_RANGES.get(preferences.get("budget", "medium"), (0, 100000))
    if lo <= product["price"] <= hi:
        reasons.append("Fits your budget range")
    return reasons
