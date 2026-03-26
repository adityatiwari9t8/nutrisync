from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from models.log import MealLog
from models.user import MacroGoal
from schemas import HistoryPoint, LoggedMealResponse, MacroGoalsPayload


def save_macro_goals(db: Session, user_id: int, goals: MacroGoalsPayload) -> MacroGoal:
    record = db.query(MacroGoal).filter(MacroGoal.user_id == user_id).first()
    if not record:
        record = MacroGoal(user_id=user_id)
        db.add(record)
    record.protein_target = goals.protein
    record.carbs_target = goals.carbs
    record.fat_target = goals.fat
    record.calorie_target = goals.calories
    db.commit()
    db.refresh(record)
    return record


def get_macro_goals(db: Session, user_id: int) -> MacroGoalsPayload:
    record = db.query(MacroGoal).filter(MacroGoal.user_id == user_id).first()
    if not record:
        return MacroGoalsPayload()
    return MacroGoalsPayload(
        protein=record.protein_target,
        carbs=record.carbs_target,
        fat=record.fat_target,
        calories=record.calorie_target,
    )


def _sum_logs(logs: list[MealLog]) -> MacroGoalsPayload:
    return MacroGoalsPayload(
        protein=round(sum(log.protein_logged for log in logs), 1),
        carbs=round(sum(log.carbs_logged for log in logs), 1),
        fat=round(sum(log.fat_logged for log in logs), 1),
        calories=round(sum(log.calories_logged for log in logs), 1),
    )


def serialize_log(log: MealLog) -> LoggedMealResponse:
    return LoggedMealResponse(
        id=log.id,
        recipe_id=log.recipe_id,
        recipe_name=log.recipe.name,
        servings=log.servings,
        protein_logged=round(log.protein_logged, 1),
        carbs_logged=round(log.carbs_logged, 1),
        fat_logged=round(log.fat_logged, 1),
        calories_logged=round(log.calories_logged, 1),
        date=log.date,
    )


def get_daily_summary(db: Session, user_id: int, on_date: date | None = None):
    target_date = on_date or datetime.utcnow().date()
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)
    logs = (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id, MealLog.date >= start, MealLog.date < end)
        .order_by(MealLog.date.desc())
        .all()
    )
    return {
        "date": target_date.isoformat(),
        "goals": get_macro_goals(db, user_id),
        "totals": _sum_logs(logs),
        "meals": [serialize_log(log) for log in logs],
    }


def _adherence(goals: MacroGoalsPayload, totals: MacroGoalsPayload) -> float:
    metrics = []
    for field in ("protein", "carbs", "fat", "calories"):
        goal_value = getattr(goals, field)
        total_value = getattr(totals, field)
        if goal_value <= 0:
            continue
        ratio = min(total_value / goal_value, 1.0)
        metrics.append(ratio)
    if not metrics:
        return 0.0
    return round(sum(metrics) / len(metrics), 2)


def get_history(db: Session, user_id: int, days: int = 7) -> list[HistoryPoint]:
    start_date = datetime.utcnow().date() - timedelta(days=days - 1)
    end_date = datetime.utcnow().date() + timedelta(days=1)
    logs = (
        db.query(MealLog)
        .filter(
            MealLog.user_id == user_id,
            MealLog.date >= datetime.combine(start_date, datetime.min.time()),
            MealLog.date < datetime.combine(end_date, datetime.min.time()),
        )
        .all()
    )

    grouped: dict[str, list[MealLog]] = defaultdict(list)
    for log in logs:
        grouped[log.date.date().isoformat()].append(log)

    goals = get_macro_goals(db, user_id)
    history: list[HistoryPoint] = []
    for offset in range(days):
        current = start_date + timedelta(days=offset)
        day_logs = grouped.get(current.isoformat(), [])
        totals = _sum_logs(day_logs)
        history.append(
            HistoryPoint(
                date=current.isoformat(),
                protein=totals.protein,
                carbs=totals.carbs,
                fat=totals.fat,
                calories=totals.calories,
                adherence=_adherence(goals, totals),
            )
        )
    return history
