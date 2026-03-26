import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models.recipe import Recipe
from models.user import PantryItem, User
from schemas import RecipeDetailResponse, RecipeRecommendationRequest, RecipeSummary
from services.macro_calculator import save_macro_goals
from services.recommender import get_recommendations

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _store_pantry_snapshot(db: Session, user_id: int, ingredients: list[str]):
    db.query(PantryItem).filter(PantryItem.user_id == user_id).delete()
    for ingredient in sorted({item.strip().lower() for item in ingredients if item.strip()}):
        db.add(PantryItem(user_id=user_id, ingredient_name=ingredient))
    db.commit()


@router.post("/recommend", response_model=list[RecipeSummary])
def recommend_recipes(
    payload: RecipeRecommendationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ingredients = [item.strip().lower() for item in payload.ingredients if item.strip()]
    if not ingredients:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one ingredient is required.")

    _store_pantry_snapshot(db, user.id, ingredients)
    save_macro_goals(db, user.id, payload.macro_goals)
    recommendations = get_recommendations(db, user, ingredients, payload.macro_goals.model_dump())
    return [RecipeSummary.model_validate(recipe) for recipe in recommendations]


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
def get_recipe(recipe_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    return RecipeDetailResponse(
        id=recipe.id,
        name=recipe.name,
        cuisine=recipe.cuisine,
        image_url=recipe.image_url,
        ingredients=json.loads(recipe.ingredients_json),
        steps=json.loads(recipe.steps_json),
        protein_g=recipe.protein_g,
        carbs_g=recipe.carbs_g,
        fat_g=recipe.fat_g,
        calories=recipe.calories,
    )
