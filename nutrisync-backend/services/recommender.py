from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.user import User, UserRating
from services import usda_service

try:
    from surprise import Dataset, Reader, SVD
except Exception:  # pragma: no cover - dependency controlled by requirements
    Dataset = Reader = SVD = None


def _normalize(text: str) -> str:
    return text.lower().strip()


def _ingredient_names(recipe: Recipe | dict[str, Any]) -> list[str]:
    ingredients = recipe["ingredients"] if isinstance(recipe, dict) else json.loads(recipe.ingredients_json)
    return [_normalize(item["name"]) for item in ingredients]


def _recipe_to_dict(recipe: Recipe) -> dict[str, Any]:
    return {
        "id": recipe.id,
        "name": recipe.name,
        "cuisine": recipe.cuisine,
        "ingredients": json.loads(recipe.ingredients_json),
        "steps": json.loads(recipe.steps_json),
        "protein_g": recipe.protein_g,
        "carbs_g": recipe.carbs_g,
        "fat_g": recipe.fat_g,
        "calories": recipe.calories,
        "image_url": recipe.image_url,
    }


def filter_by_ingredients(available_ingredients: list[str], recipe_db: list[Recipe]) -> list[dict[str, Any]]:
    available = {_normalize(item) for item in available_ingredients if item.strip()}
    scored: list[tuple[float, dict[str, Any]]] = []
    for recipe in recipe_db:
        names = _ingredient_names(recipe)
        matched = []
        for ingredient in names:
            if any(ingredient in pantry or pantry in ingredient for pantry in available):
                matched.append(ingredient)
        overlap = len(set(matched)) / max(len(set(names)), 1)
        if matched:
            recipe_dict = _recipe_to_dict(recipe)
            recipe_dict["matched_ingredients"] = sorted(set(matched))
            recipe_dict["ingredient_overlap"] = round(overlap, 3)
            scored.append((overlap, recipe_dict))

    scored.sort(key=lambda item: (item[0], item[1]["protein_g"]), reverse=True)
    if len(scored) >= 5:
        return [recipe for _, recipe in scored]

    existing_ids = {recipe["id"] for _, recipe in scored}
    for recipe in sorted(recipe_db, key=lambda item: item.protein_g, reverse=True):
        if recipe.id in existing_ids:
            continue
        recipe_dict = _recipe_to_dict(recipe)
        recipe_dict["matched_ingredients"] = []
        recipe_dict["ingredient_overlap"] = 0.0
        scored.append((0.0, recipe_dict))
        if len(scored) >= 12:
            break
    return [recipe for _, recipe in scored]


def _meal_targets(user_macro_goals: dict[str, float]) -> dict[str, float]:
    calories = user_macro_goals.get("calories", 0)
    multiplier = 1 / 3 if calories and calories > 1000 else 1
    return {
        "protein_g": user_macro_goals.get("protein", 0) * multiplier,
        "carbs_g": user_macro_goals.get("carbs", 0) * multiplier,
        "fat_g": user_macro_goals.get("fat", 0) * multiplier,
        "calories": user_macro_goals.get("calories", 0) * multiplier,
    }


def matches_macro_constraints(recipe: dict[str, Any], user_macro_goals: dict[str, float]) -> bool:
    targets = _meal_targets(user_macro_goals)
    if not any(targets.values()):
        return True
    for field, target in targets.items():
        if target <= 0:
            continue
        actual = recipe.get(field, 0)
        upper_bound = target * 1.35
        lower_bound = target * 0.25
        if actual > upper_bound:
            return False
        if field == "protein_g" and actual < lower_bound:
            return False
    return True


def macro_fit_score(recipe: dict[str, Any], user_macro_goals: dict[str, float]) -> float:
    targets = _meal_targets(user_macro_goals)
    if not any(targets.values()):
        return 1.0
    similarities = []
    for field, target in targets.items():
        if target <= 0:
            continue
        actual = recipe.get(field, 0)
        diff = abs(actual - target) / max(target, 1)
        similarities.append(max(0.0, 1.0 - diff))
    return round(sum(similarities) / max(len(similarities), 1), 3)


def compute_cosine_similarity_scores(macro_compliant: list[dict[str, Any]], preferred_ingredients: list[str]) -> dict[int, float]:
    if not macro_compliant:
        return {}
    recipe_text = [" ".join(_ingredient_names(recipe)) for recipe in macro_compliant]
    profile_text = " ".join(_normalize(item) for item in preferred_ingredients if item.strip())
    if not profile_text:
        return {recipe["id"]: 0.5 for recipe in macro_compliant}

    vectorizer = CountVectorizer(binary=True)
    matrix = vectorizer.fit_transform(recipe_text + [profile_text])
    similarities = cosine_similarity(matrix[:-1], matrix[-1]).ravel()
    return {
        macro_compliant[index]["id"]: round(float(score), 4)
        for index, score in enumerate(similarities)
    }


@dataclass
class UserProfile:
    id: int
    preferred_ingredients: list[str]


class CollaborativeFilter:
    def __init__(self):
        self._model = None
        self._global_mean = 3.5

    def fit(self, ratings: list[UserRating]):
        if not ratings or Dataset is None or Reader is None or SVD is None:
            self._model = None
            self._global_mean = 3.5
            return

        data = pd.DataFrame(
            [{"user_id": str(rating.user_id), "recipe_id": str(rating.recipe_id), "rating": float(rating.rating)} for rating in ratings]
        )
        self._global_mean = float(data["rating"].mean())
        reader = Reader(rating_scale=(1, 5))
        dataset = Dataset.load_from_df(data[["user_id", "recipe_id", "rating"]], reader)
        trainset = dataset.build_full_trainset()
        model = SVD(random_state=42, n_factors=20, n_epochs=25)
        model.fit(trainset)
        self._model = model

    def predict(self, user_id: int, recipes: list[dict[str, Any]]) -> dict[int, float]:
        if not recipes:
            return {}
        if self._model is None:
            baseline = round((self._global_mean - 1) / 4, 4)
            return {recipe["id"]: baseline for recipe in recipes}
        return {
            recipe["id"]: round((self._model.predict(str(user_id), str(recipe["id"])).est - 1) / 4, 4)
            for recipe in recipes
        }


collaborative_filter = CollaborativeFilter()


def refresh_model(db: Session):
    ratings = db.query(UserRating).all()
    collaborative_filter.fit(ratings)


def build_user_profile(db: Session, user: User, available_ingredients: list[str]) -> UserProfile:
    preferred = list({_normalize(item) for item in available_ingredients if item.strip()})
    top_ratings = (
        db.query(UserRating)
        .filter(UserRating.user_id == user.id, UserRating.rating >= 4)
        .order_by(UserRating.rating.desc())
        .all()
    )
    if top_ratings:
        recipe_lookup = {recipe.id: recipe for recipe in db.query(Recipe).filter(Recipe.id.in_([rating.recipe_id for rating in top_ratings])).all()}
        for rating in top_ratings:
            recipe = recipe_lookup.get(rating.recipe_id)
            if not recipe:
                continue
            preferred.extend(_ingredient_names(recipe))
    return UserProfile(id=user.id, preferred_ingredients=sorted(set(preferred)))


def hybrid_rank(macro_compliant: list[dict[str, Any]], cbf_scores: dict[int, float], cf_scores: dict[int, float]) -> list[dict[str, Any]]:
    ranked = []
    for recipe in macro_compliant:
        cbf_score = cbf_scores.get(recipe["id"], 0.0)
        cf_score = cf_scores.get(recipe["id"], 0.0)
        hybrid_score = round((0.6 * cbf_score) + (0.4 * cf_score), 4)
        ranked.append({**recipe, "hybrid_score": hybrid_score})
    ranked.sort(key=lambda item: (item["hybrid_score"], item["macro_fit_score"], item["waste_score"], item["protein_g"]), reverse=True)
    return ranked


def generate_optimal_recipe(
    available_ingredients: list[str],
    user_macro_goals: dict[str, float],
    user_profile: UserProfile,
    recipe_db: list[Recipe],
) -> list[dict[str, Any]]:
    candidate_recipes = filter_by_ingredients(available_ingredients, recipe_db)
    enriched = usda_service.enrich_macros(candidate_recipes)
    pantry_count = max(len(available_ingredients), 1)
    macro_compliant = []
    for recipe in enriched:
        if matches_macro_constraints(recipe, user_macro_goals):
            waste_score = len(recipe.get("matched_ingredients", [])) / pantry_count
            macro_compliant.append(
                {
                    **recipe,
                    "waste_score": round(min(waste_score, 1.0), 2),
                    "macro_fit_score": macro_fit_score(recipe, user_macro_goals),
                }
            )

    if not macro_compliant:
        macro_compliant = [
            {
                **recipe,
                "waste_score": round(len(recipe.get("matched_ingredients", [])) / pantry_count, 2),
                "macro_fit_score": macro_fit_score(recipe, user_macro_goals),
            }
            for recipe in enriched
        ]

    cbf_scores = compute_cosine_similarity_scores(macro_compliant, user_profile.preferred_ingredients)
    cf_scores = collaborative_filter.predict(user_profile.id, macro_compliant)
    ranked = hybrid_rank(macro_compliant, cbf_scores, cf_scores)
    return ranked[:5]


def get_recommendations(db: Session, user: User, available_ingredients: list[str], user_macro_goals: dict[str, float]) -> list[dict[str, Any]]:
    recipes = db.query(Recipe).all()
    user_profile = build_user_profile(db, user, available_ingredients)
    return generate_optimal_recipe(available_ingredients, user_macro_goals, user_profile, recipes)
