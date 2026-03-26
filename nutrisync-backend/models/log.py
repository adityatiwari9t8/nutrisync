from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class MealLog(Base):
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    servings: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    protein_logged: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    carbs_logged: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fat_logged: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    calories_logged: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user = relationship("User", back_populates="meal_logs")
    recipe = relationship("Recipe", back_populates="meal_logs")
