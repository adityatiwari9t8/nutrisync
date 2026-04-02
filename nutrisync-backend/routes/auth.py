from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models.user import User
from schemas import AuthLoginRequest, AuthRegisterRequest, AuthResponse, PremiumUpgradeRequest, UserResponse
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _normalize_username(value: str) -> str:
    return value.strip()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)
    normalized_username = _normalize_username(payload.username)
    if len(normalized_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 non-space characters long.",
        )

    existing_user = db.query(User).filter((User.email == normalized_email) | (User.username == normalized_username)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with that email or username already exists.")

    user = User(
        username=normalized_username,
        email=normalized_email,
        hashed_password=hash_password(payload.password),
        is_premium=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/upgrade", response_model=AuthResponse)
def upgrade_to_premium(
    payload: PremiumUpgradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_methods = {"card", "apple_pay", "upi"}
    billing_cycle = payload.billing_cycle.strip().lower()
    payment_method = payload.payment_method.strip().lower()

    if billing_cycle != "monthly":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only the monthly plan is available right now.")
    if payment_method not in allowed_methods:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a supported payment method.")

    user.is_premium = True
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))
