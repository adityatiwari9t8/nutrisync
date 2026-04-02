from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.recipe import Recipe


@dataclass(frozen=True)
class ZoneDefinition:
    key: str
    label: str
    description: str
    empty_hint: str
    keywords: tuple[str, ...]


ZONE_DEFINITIONS = (
    ZoneDefinition(
        key="protein",
        label="Protein anchors",
        description="These ingredients make dinner feel substantial and help NutriSync surface higher-protein options.",
        empty_hint="Add one protein anchor like eggs, tofu, paneer, chicken, or lentils to widen dinner options fast.",
        keywords=(
            "chicken",
            "turkey",
            "beef",
            "salmon",
            "fish",
            "shrimp",
            "egg",
            "paneer",
            "tofu",
            "lentil",
            "lentils",
            "beans",
            "rajma",
            "chickpeas",
            "soy granules",
            "greek yogurt",
            "cottage cheese",
            "milk",
            "cheese",
        ),
    ),
    ZoneDefinition(
        key="produce",
        label="Produce range",
        description="Fresh produce gives the recipe engine more flexibility and unlocks better pantry-usage combinations.",
        empty_hint="Add a little produce range with onions, tomatoes, greens, or fruit to make your pantry more versatile.",
        keywords=(
            "apple",
            "avocado",
            "banana",
            "bell pepper",
            "broccoli",
            "cabbage",
            "carrot",
            "cauliflower",
            "corn",
            "cucumber",
            "eggplant",
            "fig",
            "garlic",
            "ginger",
            "jackfruit",
            "kiwi",
            "lemon",
            "mango",
            "mushroom",
            "okra",
            "onion",
            "orange",
            "papaya",
            "peas",
            "pineapple",
            "pomegranate",
            "potato",
            "pumpkin",
            "radish",
            "spinach",
            "strawberry",
            "sweet potato",
            "tomato",
            "zucchini",
        ),
    ),
    ZoneDefinition(
        key="carb",
        label="Smart carb base",
        description="A simple carb base helps your pantry convert into complete meals instead of one-off ingredients.",
        empty_hint="A carb base like rice, bread, oats, or pasta makes your pantry much easier to turn into full meals.",
        keywords=(
            "bread",
            "rice",
            "pasta",
            "noodles",
            "tortilla",
            "oats",
            "rolled oats",
            "whole wheat tortilla",
            "whole grain bread",
            "semolina",
            "flattened rice",
            "millet",
            "quinoa",
        ),
    ),
    ZoneDefinition(
        key="booster",
        label="Flavor boosters",
        description="These pantry helpers turn basic ingredients into meals that feel more finished and intentional.",
        empty_hint="Keep at least one flavor booster around, like onion, garlic, lemon, yogurt, or oil, to make quick meals taste complete.",
        keywords=(
            "onion",
            "garlic",
            "ginger",
            "lemon",
            "olive oil",
            "sesame oil",
            "ghee",
            "greek yogurt",
            "yogurt",
            "broth",
            "parmesan",
            "cheese",
            "coffee",
        ),
    ),
)


def _normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _matches_pantry(recipe_ingredient: str, pantry: set[str]) -> bool:
    return any(recipe_ingredient in pantry_item or pantry_item in recipe_ingredient for pantry_item in pantry)


def _recipe_ingredient_names(recipe: Recipe) -> list[str]:
    ingredients = json.loads(recipe.ingredients_json)
    return sorted({_normalize(item["name"]) for item in ingredients if str(item.get("name", "")).strip()})


def _describe_zone(definition: ZoneDefinition, count: int, examples: list[str]) -> tuple[str, str]:
    if count >= 3:
        return "strong", f"Strong coverage with {', '.join(examples[:3])}. {definition.description}"
    if count >= 1:
        return "building", f"You already have {', '.join(examples[:2])}. {definition.description}"
    return "missing", definition.empty_hint


def _build_zones(ingredients: list[str]) -> list[dict]:
    zones = []
    for definition in ZONE_DEFINITIONS:
        examples = [ingredient for ingredient in ingredients if any(keyword in ingredient for keyword in definition.keywords)]
        status, description = _describe_zone(definition, len(examples), examples)
        zones.append(
            {
                "label": definition.label,
                "status": status,
                "count": len(examples),
                "description": description,
                "examples": examples[:4],
            }
        )
    return zones


def _match_recipe(recipe: Recipe, pantry: set[str]) -> dict | None:
    names = _recipe_ingredient_names(recipe)
    matched = sorted({ingredient for ingredient in names if _matches_pantry(ingredient, pantry)})
    if not matched:
        return None

    missing = [ingredient for ingredient in names if ingredient not in matched]
    gap_count = len(missing)
    match_score = round(len(matched) / max(len(names), 1), 2)

    if gap_count <= 2:
        readiness_label = "Ready with a light top-up"
    elif gap_count <= 4:
        readiness_label = "One quick grocery stop away"
    else:
        readiness_label = "Stretch pantry idea"

    return {
        "id": recipe.id,
        "name": recipe.name,
        "cuisine": recipe.cuisine,
        "image_url": recipe.image_url,
        "matched_ingredients": matched,
        "missing_ingredients": missing[:4],
        "gap_count": gap_count,
        "match_score": match_score,
        "readiness_label": readiness_label,
        "matched_count": len(matched),
        "protein_g": recipe.protein_g,
    }


def _build_unlock_suggestions(matches: list[dict]) -> list[dict]:
    unlock_counter: Counter[str] = Counter()
    recipe_examples: dict[str, list[str]] = {}

    for match in matches:
        if match["matched_count"] < 2 or not 1 <= match["gap_count"] <= 3:
            continue
        for ingredient in match["missing_ingredients"]:
            unlock_counter[ingredient] += 1
            examples = recipe_examples.setdefault(ingredient, [])
            if len(examples) < 2 and match["name"] not in examples:
                examples.append(match["name"])

    ranked = sorted(unlock_counter.items(), key=lambda item: (-item[1], item[0]))
    return [
        {
            "ingredient": ingredient,
            "unlock_count": count,
            "recipe_examples": recipe_examples.get(ingredient, []),
        }
        for ingredient, count in ranked[:4]
    ]


def _build_summary(
    ingredients: list[str],
    score_label: str,
    ready_recipe_count: int,
    next_up_recipe_count: int,
    unlock_ingredients: list[dict],
) -> str:
    if not ingredients:
        return "Scan or add ingredients to reveal what your pantry can support tonight, where it is weak, and what one ingredient would unlock next."
    if ready_recipe_count:
        if unlock_ingredients:
            top_unlock = unlock_ingredients[0]
            return (
                f"{score_label} pantry momentum. You already have {ready_recipe_count} recipes within two missing items, "
                f"and adding {top_unlock['ingredient']} could unlock {top_unlock['unlock_count']} more."
            )
        return f"{score_label} pantry momentum. You already have {ready_recipe_count} recipe options within two missing items."
    if unlock_ingredients:
        top_unlock = unlock_ingredients[0]
        return (
            f"{score_label} pantry coverage. You are still in build mode, but adding {top_unlock['ingredient']} could unlock "
            f"{top_unlock['unlock_count']} stronger recipe paths."
        )
    if next_up_recipe_count:
        return f"{score_label} pantry coverage. You are a short grocery stop away from {next_up_recipe_count} stronger dinner options."
    return f"{score_label} pantry coverage. Add a protein anchor or a carb base to give NutriSync more complete meal paths."


def build_pantry_insights(db: Session, ingredients: list[str]) -> dict:
    normalized_values = []
    for item in ingredients:
        normalized_item = _normalize(item)
        if normalized_item:
            normalized_values.append(normalized_item)
    normalized = sorted(set(normalized_values))
    zones = _build_zones(normalized)
    pantry = set(normalized)

    if not normalized:
        return {
            "pantry_score": 0,
            "score_label": "Starter",
            "summary": _build_summary([], "Starter", 0, 0, []),
            "ingredient_count": 0,
            "ready_recipe_count": 0,
            "next_up_recipe_count": 0,
            "zones": zones,
            "unlock_ingredients": [],
            "spotlight_recipes": [],
        }

    matches = [match for recipe in db.query(Recipe).all() if (match := _match_recipe(recipe, pantry))]
    matches.sort(
        key=lambda match: (
            match["gap_count"] > 2,
            match["gap_count"],
            -match["matched_count"],
            -match["match_score"],
            -match["protein_g"],
            match["name"].lower(),
        ),
    )

    ready_recipe_count = sum(1 for match in matches if match["matched_count"] >= 2 and match["gap_count"] <= 2)
    next_up_recipe_count = sum(1 for match in matches if match["matched_count"] >= 2 and 3 <= match["gap_count"] <= 4)
    unlock_ingredients = _build_unlock_suggestions(matches)

    coverage_points = sum(min(zone["count"], 2) for zone in zones) * 10
    depth_points = min(len(normalized) * 3, 20)
    readiness_points = min((ready_recipe_count * 4) + (next_up_recipe_count * 2), 20)
    pantry_score = min(100, coverage_points + depth_points + readiness_points)
    if pantry_score >= 80:
        score_label = "High"
    elif pantry_score >= 60:
        score_label = "Balanced"
    elif pantry_score >= 40:
        score_label = "Building"
    else:
        score_label = "Starter"

    spotlight_recipes = [
        {
            "id": match["id"],
            "name": match["name"],
            "cuisine": match["cuisine"],
            "image_url": match["image_url"],
            "matched_ingredients": match["matched_ingredients"],
            "missing_ingredients": match["missing_ingredients"],
            "gap_count": match["gap_count"],
            "match_score": match["match_score"],
            "readiness_label": match["readiness_label"],
        }
        for match in matches[:3]
    ]

    return {
        "pantry_score": int(pantry_score),
        "score_label": score_label,
        "summary": _build_summary(normalized, score_label, ready_recipe_count, next_up_recipe_count, unlock_ingredients),
        "ingredient_count": len(normalized),
        "ready_recipe_count": ready_recipe_count,
        "next_up_recipe_count": next_up_recipe_count,
        "zones": zones,
        "unlock_ingredients": unlock_ingredients,
        "spotlight_recipes": spotlight_recipes,
    }
