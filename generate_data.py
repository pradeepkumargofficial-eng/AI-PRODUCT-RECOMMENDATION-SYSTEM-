"""
Synthetic E-commerce Dataset Generator
---------------------------------------
Generates a realistic, internally-consistent dataset used by the recommendation
engine: products, users, purchase history, interactions (views/clicks/carts),
and reviews. Output is written as JSON files under backend/data/ so the API
can load them at startup without needing a real database.

Run:
    python generate_data.py
"""

import json
import random
from datetime import datetime, timedelta

random.seed(42)

CATEGORIES = {
    "Electronics": ["Headphones", "Smartwatch", "Bluetooth Speaker", "Laptop Stand",
                    "Wireless Mouse", "Mechanical Keyboard", "Webcam", "Power Bank"],
    "Home & Kitchen": ["Air Fryer", "Coffee Maker", "Blender", "Knife Set",
                       "Cookware Set", "Vacuum Cleaner", "Stand Mixer", "Toaster"],
    "Fitness": ["Yoga Mat", "Adjustable Dumbbells", "Resistance Bands", "Foam Roller",
                "Running Shoes", "Fitness Tracker", "Jump Rope", "Water Bottle"],
    "Fashion": ["Denim Jacket", "Running Sneakers", "Leather Wallet", "Wool Sweater",
                "Sunglasses", "Backpack", "Chino Pants", "Canvas Tote"],
    "Books": ["Sci-Fi Novel", "Productivity Guide", "Cookbook", "History Book",
              "Self-Help Book", "Programming Guide", "Biography", "Mystery Novel"],
    "Beauty": ["Face Serum", "Electric Toothbrush", "Hair Dryer", "Skincare Set",
               "Shaving Kit", "Perfume", "Makeup Palette", "Body Lotion"],
    "Office": ["Ergonomic Chair", "Standing Desk", "Desk Organizer", "Notebook Set",
               "Monitor Arm", "Desk Lamp", "Whiteboard", "Planner"],
    "Gaming": ["Gaming Headset", "Mechanical Controller", "Gaming Chair", "Mousepad",
               "Capture Card", "RGB Keyboard", "Gaming Monitor", "Headset Stand"],
}

BRANDS = ["Nova", "Aether", "Kindra", "Boltline", "Formo", "Verge", "Crestline",
          "Pulseware", "Marrow", "Solace", "Driftwood", "Ironclad", "Lumen", "Northbay"]

TAGS_POOL = ["eco-friendly", "best-seller", "premium", "budget", "new-arrival",
             "limited-stock", "highly-rated", "compact", "durable", "trending",
             "gift-idea", "minimalist", "professional", "beginner-friendly"]

INTERESTS = ["technology", "fitness", "cooking", "reading", "gaming", "fashion",
             "self-care", "productivity", "outdoors", "home-decor"]

FIRST_NAMES = ["Ava", "Liam", "Maya", "Noah", "Zoe", "Ethan", "Priya", "Omar",
               "Lucas", "Nina", "Kai", "Sofia", "Leo", "Ivy", "Ravi", "Elena"]

REVIEW_SNIPPETS = [
    "Exceeded my expectations, works great every day.",
    "Good value for the price, would buy again.",
    "Solid build quality but shipping took a while.",
    "Exactly what I needed, does the job well.",
    "A bit pricier than expected but worth it.",
    "Not bad, though the instructions could be clearer.",
    "My new favorite, using it constantly.",
    "Decent product, matches the description.",
]


def rand_price(category: str) -> float:
    ranges = {
        "Electronics": (25, 400), "Home & Kitchen": (20, 250),
        "Fitness": (10, 200), "Fashion": (15, 180),
        "Books": (8, 35), "Beauty": (10, 120),
        "Office": (20, 350), "Gaming": (20, 400),
    }
    lo, hi = ranges.get(category, (10, 200))
    return round(random.uniform(lo, hi), 2)


def generate_products(n=160):
    products = []
    pid = 1
    items = []
    for cat, names in CATEGORIES.items():
        for name in names:
            items.append((cat, name))
    while len(products) < n:
        cat, base_name = random.choice(items)
        brand = random.choice(BRANDS)
        rating = round(random.uniform(3.2, 5.0), 1)
        num_reviews = random.randint(5, 2400)
        price = rand_price(cat)
        tags = random.sample(TAGS_POOL, k=random.randint(2, 4))
        related_interest = {
            "Electronics": "technology", "Gaming": "gaming", "Fitness": "fitness",
            "Home & Kitchen": "cooking", "Fashion": "fashion", "Books": "reading",
            "Beauty": "self-care", "Office": "productivity",
        }[cat]
        products.append({
            "id": pid,
            "name": f"{brand} {base_name}",
            "category": cat,
            "brand": brand,
            "description": f"The {brand} {base_name} is a {random.choice(tags)} pick "
                            f"for anyone into {related_interest}, offering reliable "
                            f"performance for everyday use.",
            "price": price,
            "rating": rating,
            "num_reviews": num_reviews,
            "tags": tags,
            "interest": related_interest,
            "in_stock": random.random() > 0.08,
            "popularity_score": round(random.uniform(0.2, 1.0), 2),
            "image_seed": pid,
        })
        pid += 1
    return products


def generate_users(products, n=60):
    users = []
    for i in range(1, n + 1):
        name = random.choice(FIRST_NAMES) + str(i)
        interests = random.sample(INTERESTS, k=random.randint(2, 4))
        pref_categories = list({
            {"technology": "Electronics", "fitness": "Fitness", "cooking": "Home & Kitchen",
             "reading": "Books", "gaming": "Gaming", "fashion": "Fashion",
             "self-care": "Beauty", "productivity": "Office", "outdoors": "Fitness",
             "home-decor": "Home & Kitchen"}[i] for i in interests
        })
        budget = random.choice(["low", "medium", "high"])
        preferred_brands = random.sample(BRANDS, k=random.randint(1, 3))
        min_rating = random.choice([3.5, 4.0, 4.2, 4.5])

        # Purchase history: products aligned with preferred categories
        candidates = [p for p in products if p["category"] in pref_categories] or products
        history_size = random.randint(2, 8)
        purchases = random.sample(candidates, k=min(history_size, len(candidates)))

        interactions = []
        base_time = datetime(2026, 1, 1)
        for _ in range(random.randint(10, 40)):
            p = random.choice(candidates if random.random() < 0.8 else products)
            action = random.choices(
                ["view", "click", "add_to_cart", "purchase"],
                weights=[0.55, 0.25, 0.13, 0.07])[0]
            ts = base_time + timedelta(days=random.randint(0, 185),
                                        hours=random.randint(0, 23))
            interactions.append({
                "product_id": p["id"], "action": action,
                "timestamp": ts.isoformat()
            })

        reviews = []
        for p in purchases[:random.randint(0, len(purchases))]:
            reviews.append({
                "product_id": p["id"],
                "rating": round(random.uniform(3.0, 5.0), 1),
                "text": random.choice(REVIEW_SNIPPETS),
            })

        users.append({
            "id": i,
            "name": name,
            "interests": interests,
            "preferred_categories": pref_categories,
            "budget": budget,
            "preferred_brands": preferred_brands,
            "min_rating": min_rating,
            "purchase_history": [p["id"] for p in purchases],
            "interactions": interactions,
            "reviews": reviews,
        })
    return users


def main():
    products = generate_products()
    users = generate_users(products)

    with open("products.json", "w") as f:
        json.dump(products, f, indent=2)
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

    print(f"Generated {len(products)} products and {len(users)} synthetic users.")


if __name__ == "__main__":
    main()
