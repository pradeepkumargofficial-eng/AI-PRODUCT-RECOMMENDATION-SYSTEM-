"""
Lightweight sanity tests for the recommendation engine.
Run with: pytest backend/tests
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recommendation_engine.hybrid import generate_recommendations, similar_products
from recommendation_engine.content_based import content_based_scores

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(DATA_DIR, "products.json")) as f:
    PRODUCTS = json.load(f)
with open(os.path.join(DATA_DIR, "users.json")) as f:
    USERS = json.load(f)


def test_content_scores_are_bounded():
    prefs = {"categories": ["Electronics"], "interests": ["technology"],
             "budget": "medium", "brands": [], "min_rating": 4.0}
    scores = content_based_scores(PRODUCTS, prefs)
    assert all(0 <= s <= 1 for s in scores.values())


def test_recommendations_are_ranked_descending():
    prefs = {"categories": ["Fitness"], "interests": ["fitness"],
             "budget": "low", "brands": [], "min_rating": 3.5}
    recs = generate_recommendations(prefs, PRODUCTS, USERS, target_user=USERS[0], top_n=10)
    scores = [r["match_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
    assert len(recs) <= 10


def test_recommendations_exclude_out_of_stock():
    prefs = {"categories": [], "interests": [], "budget": "high", "brands": [], "min_rating": 0}
    recs = generate_recommendations(prefs, PRODUCTS, USERS, top_n=50)
    assert all(r["in_stock"] for r in recs)


def test_similar_products_excludes_self():
    target_id = PRODUCTS[0]["id"]
    similar = similar_products(target_id, PRODUCTS, top_n=5)
    assert all(p["id"] != target_id for p in similar)


def test_cold_start_user_falls_back_to_content_based():
    prefs = {"categories": ["Books"], "interests": ["reading"],
              "budget": "medium", "brands": [], "min_rating": 4.0}
    recs = generate_recommendations(prefs, PRODUCTS, USERS, target_user=None, top_n=5)
    assert len(recs) > 0
    assert all(r["score_breakdown"]["blend_alpha"] == 1.0 for r in recs)
