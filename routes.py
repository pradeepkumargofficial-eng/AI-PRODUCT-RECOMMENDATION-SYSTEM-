"""API route definitions, split out from app instantiation in main.py."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from models.schemas import RecommendationRequest
from services.data_service import data_service
from services import analytics_service
from recommendation_engine.hybrid import generate_recommendations, similar_products

router = APIRouter()


@router.get("/products", tags=["Products"])
def list_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
    sort_by: Optional[str] = Query(default=None, description="price | rating | popularity"),
    search: Optional[str] = None,
):
    """List / search / filter the product catalog."""
    products = data_service.get_products()

    if category:
        products = [p for p in products if p["category"] == category]
    if brand:
        products = [p for p in products if p["brand"] == brand]
    if min_price is not None:
        products = [p for p in products if p["price"] >= min_price]
    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if min_rating is not None:
        products = [p for p in products if p["rating"] >= min_rating]
    if in_stock_only:
        products = [p for p in products if p["in_stock"]]
    if search:
        q = search.lower()
        products = [p for p in products if q in p["name"].lower() or q in p["description"].lower()]

    if sort_by == "price":
        products = sorted(products, key=lambda p: p["price"])
    elif sort_by == "rating":
        products = sorted(products, key=lambda p: p["rating"], reverse=True)
    elif sort_by == "popularity":
        products = sorted(products, key=lambda p: p["popularity_score"], reverse=True)

    return {"count": len(products), "products": products}


@router.get("/products/{product_id}", tags=["Products"])
def get_product(product_id: int):
    product = data_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    similar = similar_products(product_id, data_service.get_products())
    return {"product": product, "similar_products": similar}


@router.get("/meta/filters", tags=["Products"])
def get_filter_options():
    """Category/brand lists used to populate filter dropdowns on the frontend."""
    return {
        "categories": data_service.categories(),
        "brands": data_service.brands(),
    }


@router.post("/recommendations", tags=["Recommendations"])
def get_recommendations(req: RecommendationRequest):
    """
    Core recommendation endpoint. Runs the hybrid engine (content-based +
    collaborative filtering) against submitted preferences and, if a
    user_id is supplied, blends in behavioral signals from that user's
    synthetic interaction history.
    """
    products = data_service.get_products()
    users = data_service.get_users()
    target_user = data_service.get_user(req.preferences.user_id) if req.preferences.user_id else None

    results = generate_recommendations(
        preferences=req.preferences.dict(),
        products=products,
        users=users,
        target_user=target_user,
        top_n=req.top_n,
    )
    return {"count": len(results), "recommendations": results}


@router.get("/users", tags=["Users"])
def list_users():
    """Lightweight list for demo purposes: lets the frontend simulate 'log in as user X'."""
    return [{"id": u["id"], "name": u["name"], "interests": u["interests"]} for u in data_service.get_users()]


@router.get("/users/{user_id}", tags=["Users"])
def get_user(user_id: int):
    user = data_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/analytics/dashboard", tags=["Analytics"])
def analytics_dashboard():
    products = data_service.get_products()
    users = data_service.get_users()
    return {
        "category_popularity": analytics_service.category_popularity(products, users),
        "engagement_trend": analytics_service.engagement_trend(users),
        "action_breakdown": analytics_service.action_breakdown(users),
        "recommendation_accuracy": analytics_service.recommendation_accuracy_proxy(users),
        "top_products": analytics_service.top_products(products),
    }


@router.get("/analytics/insights", tags=["Analytics"])
def analytics_insights():
    products = data_service.get_products()
    users = data_service.get_users()
    return {"insights": analytics_service.generate_insights(products, users)}
