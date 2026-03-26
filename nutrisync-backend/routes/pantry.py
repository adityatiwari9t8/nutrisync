from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models.user import PantryItem, User
from schemas import PantryScanResponse
from services.cv_service import detect_ingredients

router = APIRouter(prefix="/pantry", tags=["pantry"])


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
        manual_raw = form.get("ingredients")
        if manual_raw:
            manual_ingredients = [item.strip() for item in str(manual_raw).split(",") if item.strip()]
    else:
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected JSON or multipart request.") from exc
        image_base64 = payload.get("image_base64")
        manual_ingredients = payload.get("ingredients", [])

    if not image_base64 and not image_bytes and not manual_ingredients:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide an image or at least one ingredient.")

    detected = detect_ingredients(image_base64=image_base64, image_bytes=image_bytes)
    combined = detected + manual_ingredients
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
