"""
Collaborative Filtering (User-Based)
--------------------------------------
Finds users whose behavior (purchases, views, clicks, cart-adds) is
similar to the target user's behavior, then recommends products those
"neighbors" engaged with that the target user hasn't seen yet.

This captures patterns content-based filtering can't: e.g. "people who
buy standing desks also tend to buy monitor arms", even if a monitor arm
doesn't share a category/brand/interest with anything in the user's
stated preferences.
"""

from typing import Dict, List, Any
from .similarity import cosine_similarity, build_user_item_vector

K_NEIGHBORS = 8


def collaborative_scores(target_user: Dict[str, Any],
                          all_users: List[Dict[str, Any]],
                          products: List[Dict[str, Any]]) -> Dict[int, float]:
    """
    Returns {product_id: score} in [0, 1] based on weighted votes from the
    most similar users (k-nearest-neighbors in interaction space).
    """
    target_vector = build_user_item_vector(target_user)
    if not target_vector:
        return {}

    similarities = []
    for other in all_users:
        if other["id"] == target_user["id"]:
            continue
        other_vector = build_user_item_vector(other)
        sim = cosine_similarity(target_vector, other_vector)
        if sim > 0:
            similarities.append((sim, other))

    similarities.sort(key=lambda x: x[0], reverse=True)
    neighbors = similarities[:K_NEIGHBORS]

    if not neighbors:
        return {}

    raw_scores: Dict[int, float] = {}
    total_sim = sum(sim for sim, _ in neighbors) or 1.0

    already_owned = set(target_user.get("purchase_history", []))

    for sim, neighbor in neighbors:
        neighbor_vector = build_user_item_vector(neighbor)
        for pid, weight in neighbor_vector.items():
            if pid in already_owned:
                continue
            raw_scores[pid] = raw_scores.get(pid, 0.0) + sim * weight

    if not raw_scores:
        return {}

    max_score = max(raw_scores.values()) or 1.0
    return {pid: round(v / max_score, 4) for pid, v in raw_scores.items()}


def explain_collaborative_match(product_id: int, target_user: Dict[str, Any],
                                 all_users: List[Dict[str, Any]]) -> str:
    """Human-readable explanation for why collaborative filtering surfaced a product."""
    target_vector = build_user_item_vector(target_user)
    best_sim = 0.0
    for other in all_users:
        if other["id"] == target_user["id"]:
            continue
        if product_id in other.get("purchase_history", []):
            sim = cosine_similarity(target_vector, build_user_item_vector(other))
            best_sim = max(best_sim, sim)
    if best_sim > 0:
        pct = round(best_sim * 100)
        return f"Users with {pct}% similar shopping behavior purchased this product."
    return "Popular among users with similar browsing patterns."
