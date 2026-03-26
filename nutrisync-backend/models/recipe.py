from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ingredients_json: Mapped[str] = mapped_column(Text, nullable=False)
    steps_json: Mapped[str] = mapped_column(Text, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    calories: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    image_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    cuisine: Mapped[str] = mapped_column(String(120), default="Global", nullable=False)

    meal_logs = relationship("MealLog", back_populates="recipe")
    ratings = relationship("UserRating", back_populates="recipe")
