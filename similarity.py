"""
Similarity utilities
---------------------
Vectorizes products and users into simple feature spaces and computes
cosine similarity between them. Used by both collaborative filtering
(user-user similarity) and the "similar products" feature (item-item
similarity).
"""

import math
from typing import Dict, List, Any


def cosine_similarity(a: Dict[Any, float], b: Dict[Any, float]) -> float:
    """Cosine similarity between two sparse vectors represented as dicts."""
    shared_keys = set(a.keys()) & set(b.keys())
    if not shared_keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in shared_keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_user_item_vector(user: Dict[str, Any]) -> Dict[int, float]:
    """
    Builds an implicit-feedback vector for a user: product_id -> weight,
    where weight reflects how strongly the user engaged with that product
    (purchase > add_to_cart > click > view).
    """
    action_weight = {"view": 1.0, "click": 2.0, "add_to_cart": 3.0, "purchase": 5.0}
    vector: Dict[int, float] = {}
    for pid in user.get("purchase_history", []):
        vector[pid] = vector.get(pid, 0.0) + 5.0
    for interaction in user.get("interactions", []):
        w = action_weight.get(interaction["action"], 1.0)
        pid = interaction["product_id"]
        vector[pid] = vector.get(pid, 0.0) + w
    return vector


def build_product_feature_vector(product: Dict[str, Any],
                                  all_categories: List[str],
                                  all_brands: List[str]) -> Dict[str, float]:
    """One-hot-ish feature vector for a product used in item-item similarity."""
    vec: Dict[str, float] = {}
    vec[f"cat::{product['category']}"] = 1.0
    vec[f"brand::{product['brand']}"] = 1.0
    for tag in product.get("tags", []):
        vec[f"tag::{tag}"] = 0.5
    vec["price_bucket"] = round(product["price"] / 50)
    vec["rating_bucket"] = round(product["rating"])
    return vec
