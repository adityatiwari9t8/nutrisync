from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.user import MacroGoal, PantryItem, User, UserRating
from security import hash_password

RECIPES_PATH = Path(__file__).resolve().parent / "data" / "recipes.json"


def _seed_users(db: Session):
    if db.query(User).count() > 0:
        return

    demo_users = []
    for index in range(1, 13):
        demo_users.append(
            User(
                username=f"demo_user_{index}",
                email=f"demo{index}@nutrisync.dev",
                hashed_password=hash_password("demo123"),
                is_premium=index % 4 == 0,
            )
        )
    db.add_all(demo_users)
    db.commit()

    for user in demo_users:
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
    if db.query(UserRating).count() >= 100:
        return
    users = db.query(User).all()
    recipes = db.query(Recipe).all()
    if not users or not recipes:
        return

    recipe_names = {recipe.id: recipe.name.lower() for recipe in recipes}
    inserted = 0
    for user in users:
        for recipe in recipes:
            if (user.id + recipe.id) % 5 != 0 and (user.id * recipe.id) % 7 != 0:
                continue
            base_rating = 3 + ((user.id + recipe.id) % 3)
            lowered_name = recipe_names[recipe.id]
            if any(keyword in lowered_name for keyword in ["chicken", "paneer", "dal", "egg"]):
                base_rating = min(5, base_rating + 1)
            db.add(UserRating(user_id=user.id, recipe_id=recipe.id, rating=float(base_rating)))
            inserted += 1
    if inserted < 100:
        recipe_cycle = recipes[:10]
        for user in users:
            for recipe in recipe_cycle:
                db.add(UserRating(user_id=user.id, recipe_id=recipe.id, rating=float(2 + ((user.id + recipe.id) % 4))))
                inserted += 1
                if inserted >= 120:
                    break
            if inserted >= 120:
                break
    db.commit()


def seed_database(db: Session):
    _seed_users(db)
    _seed_recipes(db)
    _seed_ratings(db)
