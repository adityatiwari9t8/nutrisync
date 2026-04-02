from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models.user import PantryItem, User
from schemas import PantryIngredientUpdateRequest, PantryInsightsResponse, PantryScanResponse
from services.cv_service import SCAN_UNAVAILABLE_MESSAGE, ScanBackendUnavailable, detect_ingredients
from services.pantry_intelligence import build_pantry_insights

router = APIRouter(prefix="/pantry", tags=["pantry"])


def _parse_manual_ingredients(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        candidates = raw.split(",")
    elif isinstance(raw, (list, tuple, set)):
        candidates = list(raw)
    else:
        candidates = [raw]

    ingredients: list[str] = []
    for item in candidates:
        if item is None:
            continue
        normalized = str(item).strip()
        if normalized:
            ingredients.append(normalized)
    return ingredients


def _persist_pantry(db: Session, user_id: int, ingredients: list[str]):
    db.query(PantryItem).filter(PantryItem.user_id == user_id).delete()
    unique = []
    seen = set()
    for ingredient in ingredients:
        normalized = ingredient.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
        db.add(PantryItem(user_id=user_id, ingredient_name=normalized))
    db.commit()
    return unique


@router.post("/scan", response_model=PantryScanResponse)
async def scan_pantry(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    image_base64 = None
    image_bytes = None
    manual_ingredients: list[str] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is not None:
            image_bytes = await upload.read()
        image_base64 = form.get("image_base64")
        manual_ingredients = _parse_manual_ingredients(form.get("ingredients"))
    else:
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected JSON or multipart request.") from exc
        image_base64 = payload.get("image_base64")
        manual_ingredients = _parse_manual_ingredients(payload.get("ingredients"))

    if not image_base64 and not image_bytes and not manual_ingredients:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide an image or at least one ingredient.")

    detected: list[str] = []
    if image_base64 or image_bytes:
        try:
            detected = detect_ingredients(image_base64=image_base64, image_bytes=image_bytes)
        except ScanBackendUnavailable as exc:
            if not manual_ingredients:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=SCAN_UNAVAILABLE_MESSAGE,
                ) from exc

    combined = detected + manual_ingredients
    if not combined:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="We could not confidently identify ingredients from that image. Try a clearer scan or add ingredients manually.",
        )
    ingredients = _persist_pantry(db, user.id, combined)
    return PantryScanResponse(ingredients=ingredients)


@router.get("/ingredients", response_model=PantryScanResponse)
def get_ingredients(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ingredients = (
        db.query(PantryItem)
        .filter(PantryItem.user_id == user.id)
        .order_by(PantryItem.ingredient_name.asc())
        .all()
    )
    return PantryScanResponse(ingredients=[item.ingredient_name for item in ingredients])


@router.put("/ingredients", response_model=PantryScanResponse)
def replace_ingredients(
    payload: PantryIngredientUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ingredients = _persist_pantry(db, user.id, payload.ingredients)
    return PantryScanResponse(ingredients=ingredients)


@router.get("/insights", response_model=PantryInsightsResponse)
def get_pantry_insights(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ingredients = (
        db.query(PantryItem)
        .filter(PantryItem.user_id == user.id)
        .order_by(PantryItem.ingredient_name.asc())
        .all()
    )
    ingredient_names = [item.ingredient_name for item in ingredients]
    return PantryInsightsResponse(**build_pantry_insights(db, ingredient_names))
