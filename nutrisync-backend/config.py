import os
from pathlib import Path


def _load_local_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_local_env()

USDA_API_KEY = os.getenv("USDA_API_KEY", "YRboKJAYm057fd1P0Us9beH302V3NEOYkI5bTMKh")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nutrisync.db")
JWT_SECRET = os.getenv("JWT_SECRET", "nutrisync_jwt_secret_2024")
MOCK_CV_MODE = os.getenv("MOCK_CV_MODE", "false").lower() == "true"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
USDA_SEARCH_ENDPOINT = "https://api.nal.usda.gov/fdc/v1/foods/search"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
