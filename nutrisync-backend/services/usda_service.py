from __future__ import annotations

import json
import time
from typing import Any

import requests

from config import REDIS_URL, USDA_API_KEY, USDA_SEARCH_ENDPOINT

try:
    import redis
except Exception:  # pragma: no cover - dependency controlled by requirements
    redis = None

LOCAL_NUTRITION_FALLBACKS: dict[str, dict[str, Any]] = {
    "chicken breast": {"name": "Chicken breast", "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "calories": 165.0},
    "spinach": {"name": "Spinach", "protein_g": 2.9, "carbs_g": 3.6, "fat_g": 0.4, "calories": 23.0},
    "lentils": {"name": "Lentils", "protein_g": 9.0, "carbs_g": 20.0, "fat_g": 0.4, "calories": 116.0},
    "olive oil": {"name": "Olive oil", "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 100.0, "calories": 884.0},
    "garlic": {"name": "Garlic", "protein_g": 6.4, "carbs_g": 33.1, "fat_g": 0.5, "calories": 149.0},
    "paneer": {"name": "Paneer", "protein_g": 18.3, "carbs_g": 1.2, "fat_g": 20.8, "calories": 265.0},
    "greek yogurt": {"name": "Greek yogurt", "protein_g": 10.0, "carbs_g": 3.6, "fat_g": 0.4, "calories": 59.0},
    "egg": {"name": "Egg", "protein_g": 12.6, "carbs_g": 1.1, "fat_g": 10.6, "calories": 143.0},
    "rajma": {"name": "Kidney beans", "protein_g": 8.7, "carbs_g": 22.8, "fat_g": 0.5, "calories": 127.0},
    "tofu": {"name": "Tofu", "protein_g": 8.0, "carbs_g": 1.9, "fat_g": 4.8, "calories": 76.0},
    "onion": {"name": "Onion", "protein_g": 1.1, "carbs_g": 9.3, "fat_g": 0.1, "calories": 40.0},
    "tomato": {"name": "Tomato", "protein_g": 0.9, "carbs_g": 3.9, "fat_g": 0.2, "calories": 18.0},
    "bell pepper": {"name": "Bell pepper", "protein_g": 1.0, "carbs_g": 6.0, "fat_g": 0.3, "calories": 31.0},
    "zucchini": {"name": "Zucchini", "protein_g": 1.2, "carbs_g": 3.1, "fat_g": 0.3, "calories": 17.0},
    "lemon": {"name": "Lemon", "protein_g": 1.1, "carbs_g": 9.3, "fat_g": 0.3, "calories": 29.0},
    "ghee": {"name": "Ghee", "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 99.8, "calories": 876.0},
    "flattened rice": {"name": "Flattened rice", "protein_g": 6.5, "carbs_g": 76.9, "fat_g": 1.1, "calories": 351.0},
    "peanuts": {"name": "Peanuts", "protein_g": 25.8, "carbs_g": 16.1, "fat_g": 49.2, "calories": 567.0},
    "peas": {"name": "Peas", "protein_g": 5.4, "carbs_g": 14.5, "fat_g": 0.4, "calories": 81.0},
    "moong dal": {"name": "Moong dal", "protein_g": 24.0, "carbs_g": 63.0, "fat_g": 1.2, "calories": 347.0},
    "red lentils": {"name": "Red lentils", "protein_g": 9.0, "carbs_g": 20.0, "fat_g": 0.4, "calories": 116.0},
    "carrot": {"name": "Carrot", "protein_g": 0.9, "carbs_g": 9.6, "fat_g": 0.2, "calories": 41.0},
    "chickpeas": {"name": "Chickpeas", "protein_g": 8.9, "carbs_g": 27.4, "fat_g": 2.6, "calories": 164.0},
    "soy granules": {"name": "Soy granules", "protein_g": 52.0, "carbs_g": 33.0, "fat_g": 0.5, "calories": 345.0},
    "semolina": {"name": "Semolina", "protein_g": 12.7, "carbs_g": 73.0, "fat_g": 1.0, "calories": 360.0},
    "berries": {"name": "Berries", "protein_g": 1.0, "carbs_g": 12.0, "fat_g": 0.3, "calories": 57.0},
    "chia seeds": {"name": "Chia seeds", "protein_g": 16.5, "carbs_g": 42.1, "fat_g": 30.7, "calories": 486.0},
    "almonds": {"name": "Almonds", "protein_g": 21.2, "carbs_g": 21.6, "fat_g": 49.9, "calories": 579.0},
    "honey": {"name": "Honey", "protein_g": 0.3, "carbs_g": 82.4, "fat_g": 0.0, "calories": 304.0},
    "turkey breast": {"name": "Turkey breast", "protein_g": 29.0, "carbs_g": 0.0, "fat_g": 1.0, "calories": 135.0},
    "quinoa": {"name": "Quinoa", "protein_g": 4.4, "carbs_g": 21.3, "fat_g": 1.9, "calories": 120.0},
    "cucumber": {"name": "Cucumber", "protein_g": 0.7, "carbs_g": 3.6, "fat_g": 0.1, "calories": 15.0},
    "salmon": {"name": "Salmon", "protein_g": 20.4, "carbs_g": 0.0, "fat_g": 13.4, "calories": 208.0},
    "rice": {"name": "Rice", "protein_g": 2.7, "carbs_g": 28.0, "fat_g": 0.3, "calories": 130.0},
    "edamame": {"name": "Edamame", "protein_g": 11.9, "carbs_g": 8.9, "fat_g": 5.2, "calories": 121.0},
    "rolled oats": {"name": "Rolled oats", "protein_g": 13.2, "carbs_g": 67.7, "fat_g": 6.5, "calories": 389.0},
    "milk": {"name": "Milk", "protein_g": 3.4, "carbs_g": 5.0, "fat_g": 1.0, "calories": 42.0},
    "protein powder": {"name": "Protein powder", "protein_g": 80.0, "carbs_g": 8.0, "fat_g": 6.0, "calories": 400.0},
    "banana": {"name": "Banana", "protein_g": 1.1, "carbs_g": 22.8, "fat_g": 0.3, "calories": 89.0},
    "peanut butter": {"name": "Peanut butter", "protein_g": 25.0, "carbs_g": 20.0, "fat_g": 50.0, "calories": 588.0},
    "shrimp": {"name": "Shrimp", "protein_g": 24.0, "carbs_g": 0.2, "fat_g": 0.3, "calories": 99.0},
    "spring onion": {"name": "Spring onion", "protein_g": 1.8, "carbs_g": 7.3, "fat_g": 0.2, "calories": 32.0},
    "whole grain bread": {"name": "Whole grain bread", "protein_g": 13.0, "carbs_g": 43.0, "fat_g": 4.2, "calories": 247.0},
    "avocado": {"name": "Avocado", "protein_g": 2.0, "carbs_g": 8.5, "fat_g": 14.7, "calories": 160.0},
    "cottage cheese": {"name": "Cottage cheese", "protein_g": 11.0, "carbs_g": 3.4, "fat_g": 4.3, "calories": 98.0},
    "pumpkin seeds": {"name": "Pumpkin seeds", "protein_g": 30.2, "carbs_g": 10.7, "fat_g": 49.0, "calories": 559.0},
    "lean beef": {"name": "Lean beef", "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 15.0, "calories": 250.0},
    "black beans": {"name": "Black beans", "protein_g": 8.9, "carbs_g": 23.7, "fat_g": 0.5, "calories": 132.0},
    "corn": {"name": "Corn", "protein_g": 3.4, "carbs_g": 19.0, "fat_g": 1.5, "calories": 86.0},
    "tuna": {"name": "Tuna", "protein_g": 29.0, "carbs_g": 0.0, "fat_g": 1.0, "calories": 130.0},
    "sweet potato": {"name": "Sweet potato", "protein_g": 1.6, "carbs_g": 20.1, "fat_g": 0.1, "calories": 86.0},
    "whole wheat tortilla": {"name": "Whole wheat tortilla", "protein_g": 8.0, "carbs_g": 44.0, "fat_g": 7.0, "calories": 290.0},
    "cheese": {"name": "Cheese", "protein_g": 25.0, "carbs_g": 1.3, "fat_g": 33.0, "calories": 402.0},
    "pasta": {"name": "Pasta", "protein_g": 5.8, "carbs_g": 30.9, "fat_g": 1.1, "calories": 158.0},
    "lettuce": {"name": "Lettuce", "protein_g": 1.4, "carbs_g": 2.9, "fat_g": 0.2, "calories": 15.0},
    "turkey mince": {"name": "Turkey mince", "protein_g": 27.0, "carbs_g": 0.0, "fat_g": 8.0, "calories": 172.0},
    "couscous": {"name": "Couscous", "protein_g": 3.8, "carbs_g": 23.2, "fat_g": 0.2, "calories": 112.0},
    "bok choy": {"name": "Bok choy", "protein_g": 1.5, "carbs_g": 2.2, "fat_g": 0.2, "calories": 13.0},
    "sesame seeds": {"name": "Sesame seeds", "protein_g": 17.7, "carbs_g": 23.5, "fat_g": 49.7, "calories": 573.0},
    "sesame oil": {"name": "Sesame oil", "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 100.0, "calories": 884.0},
    "soba noodles": {"name": "Soba noodles", "protein_g": 5.1, "carbs_g": 21.4, "fat_g": 0.1, "calories": 99.0},
    "ricotta": {"name": "Ricotta", "protein_g": 11.3, "carbs_g": 3.0, "fat_g": 13.0, "calories": 174.0},
    "parmesan": {"name": "Parmesan", "protein_g": 35.8, "carbs_g": 4.1, "fat_g": 25.8, "calories": 431.0},
    "white fish": {"name": "White fish", "protein_g": 24.0, "carbs_g": 0.0, "fat_g": 1.0, "calories": 110.0},
    "millet": {"name": "Millet", "protein_g": 3.5, "carbs_g": 23.7, "fat_g": 1.0, "calories": 119.0},
    "broccoli": {"name": "Broccoli", "protein_g": 2.8, "carbs_g": 6.6, "fat_g": 0.4, "calories": 34.0}
}


class _RedisCache:
    def __init__(self):
        self._memory: dict[str, tuple[float, str]] = {}
        self._ttl_seconds = 24 * 60 * 60
        self._client = None
        if redis is not None:
            try:
                self._client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None

    def get(self, key: str) -> dict[str, Any] | None:
        if self._client:
            try:
                cached = self._client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        fallback = self._memory.get(key)
        if not fallback:
            return None
        expires_at, payload = fallback
        if expires_at < time.time():
            self._memory.pop(key, None)
            return None
        return json.loads(payload)

    def set(self, key: str, value: dict[str, Any]):
        payload = json.dumps(value)
        if self._client:
            try:
                self._client.setex(key, self._ttl_seconds, payload)
                return
            except Exception:
                pass
        self._memory[key] = (time.time() + self._ttl_seconds, payload)


cache = _RedisCache()


def _parse_food_payload(ingredient: str, payload: dict[str, Any]) -> dict[str, Any]:
    foods = payload.get("foods") or []
    if not foods:
        return LOCAL_NUTRITION_FALLBACKS.get(ingredient.lower(), {"name": ingredient.title(), "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0})

    food = foods[0]
    nutrients = {entry.get("nutrientName"): entry.get("value", 0) for entry in food.get("foodNutrients", [])}
    return {
        "name": food.get("description", ingredient.title()),
        "protein_g": float(nutrients.get("Protein", 0.0) or 0.0),
        "carbs_g": float(nutrients.get("Carbohydrate, by difference", 0.0) or 0.0),
        "fat_g": float(nutrients.get("Total lipid (fat)", 0.0) or 0.0),
        "calories": float(nutrients.get("Energy", 0.0) or 0.0),
    }


def get_ingredient_nutrition(ingredient_name: str) -> dict[str, Any]:
    normalized = ingredient_name.strip().lower()
    cache_key = f"usda:{normalized}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    if normalized in LOCAL_NUTRITION_FALLBACKS:
        parsed = LOCAL_NUTRITION_FALLBACKS[normalized]
        cache.set(cache_key, parsed)
        return parsed

    try:
        response = requests.get(
            USDA_SEARCH_ENDPOINT,
            params={"query": ingredient_name, "api_key": USDA_API_KEY},
            timeout=1,
        )
        response.raise_for_status()
        parsed = _parse_food_payload(normalized, response.json())
    except Exception:
        parsed = LOCAL_NUTRITION_FALLBACKS.get(
            normalized,
            {"name": ingredient_name.title(), "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0},
        )

    cache.set(cache_key, parsed)
    return parsed


def enrich_macros(candidate_recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for recipe in candidate_recipes:
        ingredients = recipe.get("ingredients", [])
        ingredient_macros = []
        for ingredient in ingredients:
            nutrition = get_ingredient_nutrition(ingredient["name"])
            ingredient_macros.append({"ingredient": ingredient["name"], **nutrition})
        enriched.append({**recipe, "ingredient_macros": ingredient_macros})
    return enriched
