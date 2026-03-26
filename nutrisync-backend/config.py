import os

USDA_API_KEY = os.getenv("USDA_API_KEY", "YRboKJAYm057fd1P0Us9beH302V3NEOYkI5bTMKh")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nutrisync.db")
JWT_SECRET = os.getenv("JWT_SECRET", "nutrisync_jwt_secret_2024")
MOCK_CV_MODE = os.getenv("MOCK_CV_MODE", "true").lower() == "true"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
USDA_SEARCH_ENDPOINT = "https://api.nal.usda.gov/fdc/v1/foods/search"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
