from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.user import MacroGoal, PantryItem, User, UserRating
from security import hash_password

RECIPES_PATH = Path(__file__).resolve().parent / "data" / "recipes.json"
SEEDED_USERS = [
    {
        "username": "Maya",
        "email": "demo1@nutrisync.dev",
        "is_premium": False,
    },
    {
        "username": "Arjun",
        "email": "demo4@nutrisync.dev",
        "is_premium": True,
    },
]
SEEDED_EMAILS = {user["email"] for user in SEEDED_USERS}


def _seed_users(db: Session):
    if db.query(User).count() > 0:
        return

    seeded_users = [
        User(
            username=fixture["username"],
            email=fixture["email"],
            hashed_password=hash_password("demo123"),
            is_premium=fixture["is_premium"],
        )
        for fixture in SEEDED_USERS
    ]
    db.add_all(seeded_users)
    db.commit()

    for user in seeded_users:
        db.add(
            MacroGoal(
                user_id=user.id,
                protein_target=130 if user.is_premium else 110,
                carbs_target=210 if user.is_premium else 180,
                fat_target=65 if user.is_premium else 55,
                calorie_target=2200 if user.is_premium else 1900,
            )
        )
        if user.id == 1:
            for ingredient in ["chicken breast", "spinach", "lentils", "olive oil", "garlic"]:
                db.add(PantryItem(user_id=user.id, ingredient_name=ingredient))
    db.commit()


def _seed_recipes(db: Session):
    if db.query(Recipe).count() > 0:
        return
    recipes = json.loads(RECIPES_PATH.read_text())
    for recipe in recipes:
        db.add(
            Recipe(
                id=recipe["id"],
                name=recipe["name"],
                ingredients_json=json.dumps(recipe["ingredients"]),
                steps_json=json.dumps(recipe["steps"]),
                protein_g=recipe["protein_g"],
                carbs_g=recipe["carbs_g"],
                fat_g=recipe["fat_g"],
                calories=recipe["calories"],
                image_url=recipe.get("image_url", ""),
                cuisine=recipe.get("cuisine", "Global"),
            )
        )
    db.commit()


def _seed_ratings(db: Session):
    recipes = db.query(Recipe).all()
    seeded_users = db.query(User).filter(User.email.in_(sorted(SEEDED_EMAILS))).order_by(User.id.asc()).all()
    if not recipes or len(seeded_users) != len(SEEDED_USERS):
        return

    existing_pairs = {
        (user_id, recipe_id)
        for user_id, recipe_id in (
            db.query(UserRating.user_id, UserRating.recipe_id)
            .filter(UserRating.user_id.in_([user.id for user in seeded_users]))
            .all()
        )
    }
    if len(existing_pairs) >= len(seeded_users) * len(recipes):
        return

    recipe_names = {recipe.id: recipe.name.lower() for recipe in recipes}
    for user in seeded_users:
        for recipe in recipes:
            if (user.id, recipe.id) in existing_pairs:
                continue
            base_rating = 3 + ((user.id + recipe.id) % 3)
            lowered_name = recipe_names[recipe.id]
            if any(keyword in lowered_name for keyword in ["chicken", "paneer", "dal", "egg"]):
                base_rating = min(5, base_rating + 1)
            if user.is_premium and any(keyword in lowered_name for keyword in ["salmon", "tofu", "quinoa", "greek"]):
                base_rating = min(5, base_rating + 1)
            db.add(UserRating(user_id=user.id, recipe_id=recipe.id, rating=float(base_rating)))
    db.commit()


def seed_database(db: Session):
    _seed_users(db)
    _seed_recipes(db)
    _seed_ratings(db)
