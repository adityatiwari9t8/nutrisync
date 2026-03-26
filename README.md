# NutriSync

NutriSync is a full-stack AI-powered meal recommendation platform that closes the pantry-to-macro gap. Users can scan their pantry or fridge, detect ingredients, enrich nutrition data through USDA FoodData Central, rank recipes with a hybrid recommender, track daily macros, and unlock a premium dietitian portal.

## Stack

- Frontend: React, Vite, TailwindCSS, Axios, Framer Motion, Recharts
- Backend: FastAPI, Uvicorn, SQLAlchemy, JWT auth
- ML and data: scikit-learn, pandas, numpy, Pillow, torchvision MobileNetV2, scikit-surprise SVD
- Database: SQLite in development, PostgreSQL-ready through SQLAlchemy
- Cache: Redis with 24-hour USDA response caching and in-memory fallback when Redis is unavailable

## Project Structure

```text
nutrisync-backend/
  main.py
  routes/
  services/
  models/
  data/recipes.json
  requirements.txt

nutrisync-frontend/
  src/
  package.json
```

## Features

- JWT register and login flow with localStorage token persistence
- Pantry scan flow supporting multipart uploads, base64 payloads, and direct camera capture from the frontend
- Real MobileNetV2 pantry scanning, with an optional mock mode for deterministic local testing
- USDA FoodData Central integration with Redis cache keys in the form `usda:{ingredient_name}`
- Hybrid recipe recommender using content similarity plus collaborative filtering
- 50 seeded recipes with full ingredients, macros, and step-by-step instructions
- 100+ seeded mock user-recipe ratings for SVD training
- Daily macro tracker with current-day summary and 7-day history
- Premium dietitian portal with averages, trends, nutrition history, and a demo dietitian session-request flow
- Responsive frontend with mobile-first layouts, empty states, and animated page transitions

## Environment Variables

Backend defaults live in [`nutrisync-backend/.env.example`](./nutrisync-backend/.env.example):

```env
USDA_API_KEY=YRboKJAYm057fd1P0Us9beH302V3NEOYkI5bTMKh
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./nutrisync.db
JWT_SECRET=nutrisync_jwt_secret_2024
MOCK_CV_MODE=false
FRONTEND_ORIGIN=http://localhost:5173
```

Frontend example:

```env
VITE_API_URL=http://localhost:8000
```

## Setup

1. `cd nutrisync-backend`
2. `pip install -r requirements.txt`
3. `cp .env.example .env`
4. Start Redis with `redis-server`
5. Run the API with `uvicorn main:app --reload`

In a second terminal:

1. `cd nutrisync-frontend`
2. `npm install`
3. `cp .env.example .env`
4. Run the frontend with `npm run dev`

The frontend is served on `http://localhost:5173` and the backend on `http://localhost:8000`.

With `MOCK_CV_MODE=false`, the first real pantry scan may take a little longer while torchvision downloads the MobileNetV2 weights locally.

## One-Command Start and Stop

After the initial dependency install, start the full stack from the project root with:

```bash
./start.sh
```

Stop the managed Redis, backend, and frontend processes with:

```bash
./end.sh
```

The start script writes process logs to `.nutrisync/logs/`.

## Demo Accounts

Seed data creates 12 demo users with password `demo123`.

- Free tier example: `demo1@nutrisync.dev`
- Premium example: `demo4@nutrisync.dev`

You can also register new accounts from the UI.

## API Surface

- `POST /auth/register`
- `POST /auth/login`
- `POST /pantry/scan`
- `GET /pantry/ingredients`
- `POST /recipes/recommend`
- `GET /recipes/{id}`
- `POST /tracker/log`
- `GET /tracker/daily`
- `GET /tracker/history`
- `GET /dietitian/concierge`
- `POST /dietitian/request-session`
- `GET /dietitian/dashboard`
- `GET /health`

## Notes

- `MOCK_CV_MODE=false` enables real image-based ingredient scanning. Switch it to `true` only if you want deterministic mock detections for quick testing.
- If the model cannot confidently map the scan to ingredient labels, the pantry API returns a clear validation error so the user can retry with a cleaner image or add ingredients manually.
- If Redis or USDA are unavailable, the app falls back gracefully so the recommendation flow still works in local development.
- The backend seeds recipes, demo users, macro goals, pantry ingredients, and collaborative filtering ratings on startup.
