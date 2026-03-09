from fastapi import FastAPI, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _allow_credentials(origins: list[str]) -> bool:
    return "*" not in origins


async def seed_plans():
    existing = await db.plans.count_documents({})
    if existing > 0:
        return
    plans = [
        {
            "id": "free",
            "name": "Graze",
            "name_pt": "Graze (Grátis)",
            "price_usd": 0,
            "quotas": {
                "nutrition_photo": {"limit": 3, "period": "monthly"},
                "nutrition_text": {"limit": -1, "period": "monthly"},
                "meal_plan": {"limit": 1, "period": "weekly"},
                "agenda_actions": {"limit": 15, "period": "monthly"},
                "reminders_email": {"limit": 20, "period": "monthly"},
                "reminders_whatsapp": {"limit": 5, "period": "monthly"},
                "finance_reminders": {"limit": 17, "period": "monthly"},
                "finance_analysis": {"limit": 7, "period": "monthly"},
            }
        },
        {
            "id": "pro",
            "name": "Boost",
            "name_pt": "Boost (Pro)",
            "price_usd": 24,
            "quotas": {
                "nutrition_photo": {"limit": 90, "period": "monthly"},
                "nutrition_text": {"limit": -1, "period": "monthly"},
                "meal_plan": {"limit": 1, "period": "daily"},
                "agenda_actions": {"limit": -1, "period": "monthly"},
                "reminders_email": {"limit": 200, "period": "monthly"},
                "reminders_whatsapp": {"limit": 60, "period": "monthly"},
                "finance_reminders": {"limit": 60, "period": "monthly"},
                "finance_analysis": {"limit": 30, "period": "monthly"},
            }
        },
        {
            "id": "premium",
            "name": "Thrive",
            "name_pt": "Thrive (Premium)",
            "price_usd": 39,
            "quotas": {
                "nutrition_photo": {"limit": 200, "period": "monthly"},
                "nutrition_text": {"limit": -1, "period": "monthly"},
                "meal_plan": {"limit": 1, "period": "daily"},
                "agenda_actions": {"limit": -1, "period": "monthly"},
                "reminders_email": {"limit": 1000, "period": "monthly"},
                "reminders_whatsapp": {"limit": 200, "period": "monthly"},
                "finance_reminders": {"limit": 200, "period": "monthly"},
                "finance_analysis": {"limit": 100, "period": "monthly"},
            }
        }
    ]
    await db.plans.insert_many(plans)
    logger.info("Seeded plans")


async def seed_food_database():
    existing = await db.foods.count_documents({})
    if existing > 0:
        return
    food_file = ROOT_DIR / 'data' / 'food_database.json'
    if food_file.exists():
        with open(food_file, 'r', encoding='utf-8') as f:
            foods = json.load(f)
        await db.foods.insert_many(foods)
        await db.foods.create_index("name_pt")
        await db.foods.create_index("name_en")
        await db.foods.create_index("keywords")
        logger.info(f"Seeded {len(foods)} foods")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_plans()
    await seed_food_database()
    yield
    client.close()

app = FastAPI(title="Life OS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_credentials(_cors_origins()),
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from routes.auth import router as auth_router
from routes.nutrition import router as nutrition_router
from routes.agenda import router as agenda_router
from routes.finance import router as finance_router
from routes.chat import router as chat_router
from routes.user import router as user_router
from routes.plaid import router as plaid_router

app.include_router(auth_router)
app.include_router(nutrition_router)
app.include_router(agenda_router)
app.include_router(finance_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(plaid_router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/api")
async def root():
    return {"message": "Life OS API v1.0"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
