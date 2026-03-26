from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies import get_db, require_premium
from models.user import DietitianSessionRequest, User
from schemas import (
    DietitianConciergeResponse,
    DietitianDashboardResponse,
    DietitianProfileResponse,
    DietitianSessionRequestPayload,
    DietitianSessionRequestResponse,
    MacroGoalsPayload,
    UserResponse,
)
from services.macro_calculator import get_history

router = APIRouter(prefix="/dietitian", tags=["dietitian"])

DEMO_DIETITIAN = {
    "name": "Dr. Meera Sharma, RD",
    "title": "Sports Dietitian & Metabolic Health Coach",
    "credentials": "MSc Clinical Nutrition, Registered Dietitian",
    "bio": (
        "Meera works with busy professionals who want higher-protein meals, steadier energy, "
        "and simpler weekly food decisions without losing familiar cuisines."
    ),
    "specialties": [
        "High-protein meal planning",
        "Indian and vegetarian macros",
        "Weight management",
        "Strength training nutrition",
    ],
    "response_time": "Usually confirms within 4 business hours",
    "session_modes": ["Video consult", "7-day chat follow-up"],
}


def _format_slot(slot: datetime) -> str:
    time_label = slot.strftime("%I:%M %p").lstrip("0")
    return f"{slot.strftime('%B')} {slot.day}, {slot.year} at {time_label}"


def _build_demo_openings() -> list[str]:
    now = datetime.now()
    slot_blueprints = [(1, 11, 30), (1, 18, 0), (2, 10, 0)]
    openings: list[datetime] = []

    for days_ahead, hour, minute in slot_blueprints:
        candidate = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        openings.append(candidate)

    openings.sort()
    return [_format_slot(slot) for slot in openings]


def _build_demo_profile() -> DietitianProfileResponse:
    return DietitianProfileResponse(
        **DEMO_DIETITIAN,
        next_openings=_build_demo_openings(),
    )


def _get_latest_request(db: Session, user_id: int) -> DietitianSessionRequest | None:
    return (
        db.query(DietitianSessionRequest)
        .filter(DietitianSessionRequest.user_id == user_id)
        .order_by(DietitianSessionRequest.updated_at.desc(), DietitianSessionRequest.id.desc())
        .first()
    )


@router.get("/concierge", response_model=DietitianConciergeResponse)
def dietitian_concierge(user: User = Depends(require_premium), db: Session = Depends(get_db)):
    latest_request = _get_latest_request(db, user.id)
    return DietitianConciergeResponse(
        dietitian=_build_demo_profile(),
        latest_request=DietitianSessionRequestResponse.model_validate(latest_request) if latest_request else None,
    )


@router.post("/request-session", response_model=DietitianSessionRequestResponse)
def request_dietitian_session(
    payload: DietitianSessionRequestPayload,
    user: User = Depends(require_premium),
    db: Session = Depends(get_db),
):
    openings = _build_demo_openings()
    preferred_slot = (payload.preferred_slot or "").strip()
    if preferred_slot not in openings:
        preferred_slot = openings[0]

    latest_request = _get_latest_request(db, user.id)
    if latest_request:
        latest_request.dietitian_name = DEMO_DIETITIAN["name"]
        latest_request.status = "confirmed"
        latest_request.preferred_slot = preferred_slot
        latest_request.goal_focus = payload.goal_focus.strip() or "Macro alignment and meal planning"
        latest_request.notes = payload.notes.strip()
        latest_request.session_mode = DEMO_DIETITIAN["session_modes"][0]
        latest_request.updated_at = datetime.utcnow()
        request_record = latest_request
    else:
        request_record = DietitianSessionRequest(
            user_id=user.id,
            dietitian_name=DEMO_DIETITIAN["name"],
            status="confirmed",
            preferred_slot=preferred_slot,
            goal_focus=payload.goal_focus.strip() or "Macro alignment and meal planning",
            notes=payload.notes.strip(),
            session_mode=DEMO_DIETITIAN["session_modes"][0],
        )
        db.add(request_record)

    db.commit()
    db.refresh(request_record)
    return DietitianSessionRequestResponse.model_validate(request_record)


@router.get("/dashboard", response_model=DietitianDashboardResponse)
def dietitian_dashboard(user: User = Depends(require_premium), db: Session = Depends(get_db)):
    history = get_history(db, user.id, 14)
    if history:
        averages = MacroGoalsPayload(
            protein=round(sum(point.protein for point in history) / len(history), 1),
            carbs=round(sum(point.carbs for point in history) / len(history), 1),
            fat=round(sum(point.fat for point in history) / len(history), 1),
            calories=round(sum(point.calories for point in history) / len(history), 1),
        )
    else:
        averages = MacroGoalsPayload()

    trends = {
        "protein_trend": round(history[-1].protein - history[0].protein, 1) if len(history) > 1 else 0.0,
        "carbs_trend": round(history[-1].carbs - history[0].carbs, 1) if len(history) > 1 else 0.0,
        "fat_trend": round(history[-1].fat - history[0].fat, 1) if len(history) > 1 else 0.0,
        "calorie_trend": round(history[-1].calories - history[0].calories, 1) if len(history) > 1 else 0.0,
    }

    meals = [
        {
            "date": point.date,
            "protein": point.protein,
            "carbs": point.carbs,
            "fat": point.fat,
            "calories": point.calories,
            "adherence": point.adherence,
        }
        for point in history
    ]

    return DietitianDashboardResponse(
        user=UserResponse.model_validate(user),
        averages=averages,
        trends=trends,
        history=history,
        meals=meals,
    )
