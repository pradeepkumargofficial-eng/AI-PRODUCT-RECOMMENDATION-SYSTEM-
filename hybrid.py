"""
Hybrid Recommendation Engine
------------------------------
Combines content-based filtering (works instantly, even for new users)
with collaborative filtering (captures "wisdom of the crowd" patterns)
into a single ranked list, with a match percentage and explanation for
every recommendation. This is the main entry point the API calls.

Blend strategy:
    final_score = alpha * content_score + (1 - alpha) * collaborative_score

`alpha` adapts to how much collaborative signal is available: a user with
little history leans on content-based (alpha -> 0.85); a user with rich
history gets more weight from collaborative filtering (alpha -> 0.5).
This mirrors what production recommenders do to solve the "cold start"
problem.
"""

from typing import Dict, List, Any
from .content_based import content_based_scores, explain_content_match
from .collaborative import collaborative_scores, explain_collaborative_match


def _adaptive_alpha(target_user: Dict[str, Any]) -> float:
    history_len = len(target_user.get("purchase_history", [])) + \
        len(target_user.get("interactions", []))
    if history_len == 0:
        return 1.0  # pure content-based, cold start
    if history_len < 10:
        return 0.8
    if history_len < 25:
        return 0.65
    return 0.5


def generate_recommendations(preferences: Dict[str, Any],
                              products: List[Dict[str, Any]],
                              users: List[Dict[str, Any]],
                              target_user: Dict[str, Any] = None,
                              top_n: int = 12) -> List[Dict[str, Any]]:
    """
    Returns a ranked list of product dicts, each annotated with:
        - match_score (0-100 int, "match percentage")
        - explanation (string)
        - score_breakdown (content vs collaborative contribution)
    """
    content_scores = content_based_scores(products, preferences)

    collab_scores: Dict[int, float] = {}
    alpha = 1.0
    if target_user is not None:
        collab_scores = collaborative_scores(target_user, users, products)
        alpha = _adaptive_alpha(target_user)
        if not collab_scores:
            alpha = 1.0  # no neighbors found, fall back to content-only

    ranked = []
    for p in products:
        if not p.get("in_stock", True):
            continue
        c_score = content_scores.get(p["id"], 0.0)
        cf_score = collab_scores.get(p["id"], 0.0)
        final = alpha * c_score + (1 - alpha) * cf_score
        # Small popularity nudge as a tie-breaker, mimicking real systems
        # that blend in global popularity signals.
        final = 0.92 * final + 0.08 * p.get("popularity_score", 0.5)

        reasons = explain_content_match(p, preferences)
        explanation = reasons[0] if reasons else "Matches overall trends among similar shoppers."
        if cf_score > c_score and target_user is not None and collab_scores:
            explanation = explain_collaborative_match(p["id"], target_user, users)

        ranked.append({
            **p,
            "match_score": round(final * 100),
            "explanation": explanation,
            "score_breakdown": {
                "content_based": round(c_score * 100),
                "collaborative": round(cf_score * 100),
                "blend_alpha": round(alpha, 2),
            },
        })

    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked[:top_n]


def similar_products(product_id: int, products: List[Dict[str, Any]],
                      top_n: int = 4) -> List[Dict[str, Any]]:
    """Item-item similarity: 'customers who viewed this also viewed'."""
    from .similarity import build_product_feature_vector, cosine_similarity

    categories = list({p["category"] for p in products})
    brands = list({p["brand"] for p in products})
    target = next((p for p in products if p["id"] == product_id), None)
    if target is None:
        return []

    target_vec = build_product_feature_vector(target, categories, brands)
    scored = []
    for p in products:
        if p["id"] == product_id:
            continue
        vec = build_product_feature_vector(p, categories, brands)
        sim = cosine_similarity(target_vec, vec)
        scored.append((sim, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{**p, "similarity": round(sim * 100)} for sim, p in scored[:top_n]]
