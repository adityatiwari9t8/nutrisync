from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models.user import User
from schemas import AuthLoginRequest, AuthRegisterRequest, AuthResponse, PremiumUpgradeRequest, UserResponse
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with that email or username already exists.")

    user = User(
        username=payload.username,
        email=payload.email,
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
    user = db.query(User).filter(User.email == payload.email).first()
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
    if payload.billing_cycle != "monthly":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only the monthly plan is available right now.")
    if payload.payment_method not in allowed_methods:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a supported payment method.")

    user.is_premium = True
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))
