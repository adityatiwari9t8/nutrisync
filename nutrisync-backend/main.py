from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import FRONTEND_ORIGIN
from database import Base, SessionLocal, engine
from routes.auth import router as auth_router
from routes.dietitian import router as dietitian_router
from routes.pantry import router as pantry_router
from routes.recipes import router as recipes_router
from routes.tracker import router as tracker_router
from seed import seed_database
from services.recommender import refresh_model

app = FastAPI(title="NutriSync API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    message = "; ".join(error["msg"] for error in exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": message, "detail": message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    message = "Internal server error."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": message, "detail": message},
    )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        refresh_model(db)
    finally:
        db.close()


app.include_router(auth_router)
app.include_router(pantry_router)
app.include_router(recipes_router)
app.include_router(tracker_router)
app.include_router(dietitian_router)


@app.get("/health")
def health():
    return {"status": "ok"}
