from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models.log import MealLog
from models.recipe import Recipe
from models.user import User
from schemas import DailyTrackerResponse, TrackerLogRequest
from services.macro_calculator import get_daily_summary, get_history

router = APIRouter(prefix="/tracker", tags=["tracker"])


@router.post("/log")
def log_meal(payload: TrackerLogRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == payload.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")

    meal_log = MealLog(
        user_id=user.id,
        recipe_id=recipe.id,
        servings=payload.servings,
        protein_logged=recipe.protein_g * payload.servings,
        carbs_logged=recipe.carbs_g * payload.servings,
        fat_logged=recipe.fat_g * payload.servings,
        calories_logged=recipe.calories * payload.servings,
    )
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)

    return {
        "message": "Meal logged successfully.",
        "meal": {
            "id": meal_log.id,
            "recipe_id": meal_log.recipe_id,
            "servings": meal_log.servings,
            "protein_logged": round(meal_log.protein_logged, 1),
            "carbs_logged": round(meal_log.carbs_logged, 1),
            "fat_logged": round(meal_log.fat_logged, 1),
            "calories_logged": round(meal_log.calories_logged, 1),
            "date": meal_log.date.isoformat(),
        },
    }


@router.get("/daily", response_model=DailyTrackerResponse)
def daily_tracker(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return DailyTrackerResponse(**get_daily_summary(db, user.id))


@router.get("/history")
def tracker_history(
    days: int = Query(default=7, ge=1, le=30),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"history": get_history(db, user.id, days)}
