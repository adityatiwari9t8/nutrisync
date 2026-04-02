from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MacroGoalsPayload(BaseModel):
    protein: float = Field(default=0, ge=0)
    carbs: float = Field(default=0, ge=0)
    fat: float = Field(default=0, ge=0)
    calories: float = Field(default=0, ge=0)


class IngredientPayload(BaseModel):
    name: str
    quantity: str | None = None
    unit: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_premium: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    is_premium: bool = False


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class PremiumUpgradeRequest(BaseModel):
    billing_cycle: str = Field(default="monthly", max_length=20)
    payment_method: str = Field(min_length=2, max_length=40)
    cardholder_name: str = Field(default="", max_length=80)
    card_last4: str = Field(default="", max_length=4)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PantryScanRequest(BaseModel):
    image_base64: str | None = None
    ingredients: list[str] = Field(default_factory=list)


class PantryScanResponse(BaseModel):
    ingredients: list[str]


class PantryIngredientUpdateRequest(BaseModel):
    ingredients: list[str] = Field(default_factory=list)


class PantryZoneInsight(BaseModel):
    label: str
    status: str
    count: int
    description: str
    examples: list[str] = Field(default_factory=list)


class PantryUnlockSuggestion(BaseModel):
    ingredient: str
    unlock_count: int
    recipe_examples: list[str] = Field(default_factory=list)


class PantrySpotlightRecipe(BaseModel):
    id: int
    name: str
    cuisine: str
    image_url: str
    matched_ingredients: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)
    gap_count: int
    match_score: float
    readiness_label: str


class PantryInsightsResponse(BaseModel):
    pantry_score: int
    score_label: str
    summary: str
    ingredient_count: int
    ready_recipe_count: int
    next_up_recipe_count: int
    zones: list[PantryZoneInsight] = Field(default_factory=list)
    unlock_ingredients: list[PantryUnlockSuggestion] = Field(default_factory=list)
    spotlight_recipes: list[PantrySpotlightRecipe] = Field(default_factory=list)


class RecipeRecommendationRequest(BaseModel):
    ingredients: list[str] = Field(default_factory=list)
    macro_goals: MacroGoalsPayload = Field(default_factory=MacroGoalsPayload)


class RecipeIngredient(BaseModel):
    name: str
    quantity: str
    unit: str


class RecipeSummary(BaseModel):
    id: int
    name: str
    cuisine: str
    matched_ingredients: list[str] = Field(default_factory=list)
    protein_g: float
    carbs_g: float
    fat_g: float
    calories: float
    image_url: str
    waste_score: float
    hybrid_score: float
    macro_fit_score: float


class RecipeDetailResponse(BaseModel):
    id: int
    name: str
    cuisine: str
    image_url: str
    ingredients: list[RecipeIngredient]
    steps: list[str]
    protein_g: float
    carbs_g: float
    fat_g: float
    calories: float


class TrackerLogRequest(BaseModel):
    recipe_id: int
    servings: float = Field(default=1.0, gt=0)


class LoggedMealResponse(BaseModel):
    id: int
    recipe_id: int
    recipe_name: str
    servings: float
    protein_logged: float
    carbs_logged: float
    fat_logged: float
    calories_logged: float
    date: datetime


class DailyTrackerResponse(BaseModel):
    date: str
    goals: MacroGoalsPayload
    totals: MacroGoalsPayload
    meals: list[LoggedMealResponse]


class HistoryPoint(BaseModel):
    date: str
    protein: float
    carbs: float
    fat: float
    calories: float
    adherence: float


class DietitianDashboardResponse(BaseModel):
    user: UserResponse
    averages: MacroGoalsPayload
    trends: dict[str, float]
    history: list[HistoryPoint]
    meals: list[dict[str, Any]]


class DietitianProfileResponse(BaseModel):
    name: str
    title: str
    credentials: str
    bio: str
    specialties: list[str] = Field(default_factory=list)
    response_time: str
    session_modes: list[str] = Field(default_factory=list)
    next_openings: list[str] = Field(default_factory=list)


class DietitianSessionRequestPayload(BaseModel):
    preferred_slot: str | None = Field(default=None, max_length=120)
    goal_focus: str = Field(default="", max_length=160)
    notes: str = Field(default="", max_length=600)


class DietitianSessionRequestResponse(BaseModel):
    id: int
    dietitian_name: str
    status: str
    preferred_slot: str
    goal_focus: str
    notes: str
    session_mode: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DietitianConciergeResponse(BaseModel):
    dietitian: DietitianProfileResponse
    latest_request: DietitianSessionRequestResponse | None = None
