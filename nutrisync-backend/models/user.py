from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    macro_goal = relationship("MacroGoal", back_populates="user", uselist=False, cascade="all, delete-orphan")
    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    pantry_items = relationship("PantryItem", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("UserRating", back_populates="user", cascade="all, delete-orphan")
    dietitian_requests = relationship("DietitianSessionRequest", back_populates="user", cascade="all, delete-orphan")


class MacroGoal(Base):
    __tablename__ = "macro_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    protein_target: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    carbs_target: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fat_target: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    calorie_target: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user = relationship("User", back_populates="macro_goal")


class PantryItem(Base):
    __tablename__ = "pantry_items"
    __table_args__ = (UniqueConstraint("user_id", "ingredient_name", name="uq_user_ingredient"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    ingredient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="pantry_items")


class UserRating(Base):
    __tablename__ = "user_ratings"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_rating"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)

    user = relationship("User", back_populates="ratings")
    recipe = relationship("Recipe", back_populates="ratings")


class DietitianSessionRequest(Base):
    __tablename__ = "dietitian_session_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    dietitian_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="confirmed", nullable=False)
    preferred_slot: Mapped[str] = mapped_column(String(120), nullable=False)
    goal_focus: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    notes: Mapped[str] = mapped_column(String(600), default="", nullable=False)
    session_mode: Mapped[str] = mapped_column(String(80), default="Video consult", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="dietitian_requests")
