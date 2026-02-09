from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/nutrition", tags=["Nutrition"])
logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


class PhotoAnalysisRequest(BaseModel):
    image_base64: str
    meal_type: Optional[str] = None


class TextAnalysisRequest(BaseModel):
    text: str
    meal_type: Optional[str] = None


class MealPlanRequest(BaseModel):
    regenerate: bool = False


@router.post("/analyze-photo")
async def analyze_photo(req: PhotoAnalysisRequest, request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    from services.ai_provider import analyze_food_photo
    from services.nutrition_db import calculate_meal_nutrients

    current = await get_current_user(request)
    user_id = current["user_id"]

    quota = await check_quota(user_id, "nutrition_photo")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail=f"Limite de fotos atingido ({quota['limit']}/mês). Faça upgrade do plano.")

    ai_result = await analyze_food_photo(req.image_base64)
    if "error" in ai_result:
        raise HTTPException(status_code=422, detail=ai_result["error"])

    items = ai_result.get("items", [])
    nutrition = await calculate_meal_nutrients(items)

    meal_id = str(uuid.uuid4())
    meal = {
        "id": meal_id,
        "user_id": user_id,
        "type": "photo",
        "meal_type": req.meal_type or ai_result.get("meal_type", "refeição"),
        "items": nutrition["items"],
        "total_nutrients": nutrition["total"],
        "ai_raw_response": ai_result,
        "has_photo": True,
        "notes": ai_result.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.meals.insert_one(meal)
    await increment_quota(user_id, "nutrition_photo")

    await _db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": "nutrition_photo_analysis",
        "details": {"meal_id": meal_id, "items_detected": len(items), "ai_response": ai_result},
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "meal_id": meal_id,
        "meal_type": meal["meal_type"],
        "items": nutrition["items"],
        "total": nutrition["total"],
        "notes": ai_result.get("notes", ""),
        "unmatched_items": [i for i in nutrition["items"] if not i.get("matched")]
    }


@router.post("/analyze-text")
async def analyze_text(req: TextAnalysisRequest, request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    from services.ai_provider import analyze_food_text
    from services.nutrition_db import calculate_meal_nutrients

    current = await get_current_user(request)
    user_id = current["user_id"]

    ai_result = await analyze_food_text(req.text)
    if "error" in ai_result:
        raise HTTPException(status_code=422, detail=ai_result["error"])

    items = ai_result.get("items", [])
    nutrition = await calculate_meal_nutrients(items)

    meal_id = str(uuid.uuid4())
    meal = {
        "id": meal_id,
        "user_id": user_id,
        "type": "text",
        "meal_type": req.meal_type or ai_result.get("meal_type", "refeição"),
        "original_text": req.text,
        "items": nutrition["items"],
        "total_nutrients": nutrition["total"],
        "ai_raw_response": ai_result,
        "has_photo": False,
        "notes": ai_result.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.meals.insert_one(meal)

    await _db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": "nutrition_text_analysis",
        "details": {"meal_id": meal_id, "original_text": req.text, "items_detected": len(items)},
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "meal_id": meal_id,
        "meal_type": meal["meal_type"],
        "items": nutrition["items"],
        "total": nutrition["total"],
        "notes": ai_result.get("notes", "")
    }


@router.get("/meals")
async def get_meals(request: Request, limit: int = 20, offset: int = 0):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    meals = await _db.meals.find(
        {"user_id": current["user_id"]},
        {"_id": 0, "ai_raw_response": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await _db.meals.count_documents({"user_id": current["user_id"]})
    return {"meals": meals, "total": total}


@router.get("/dashboard")
async def get_nutrition_dashboard(request: Request, period: str = "week"):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    user_id = current["user_id"]

    now = datetime.now(timezone.utc)
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - __import__('datetime').timedelta(days=7)
    else:
        start = now - __import__('datetime').timedelta(days=30)

    meals = await _db.meals.find(
        {"user_id": user_id, "created_at": {"$gte": start.isoformat()}},
        {"_id": 0, "ai_raw_response": 0}
    ).sort("created_at", -1).to_list(1000)

    daily_stats = {}
    for meal in meals:
        date_key = meal["created_at"][:10]
        if date_key not in daily_stats:
            daily_stats[date_key] = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals_count": 0}
        total = meal.get("total_nutrients", {})
        daily_stats[date_key]["calories"] += total.get("calories", 0)
        daily_stats[date_key]["protein_g"] += total.get("protein_g", 0)
        daily_stats[date_key]["carbs_g"] += total.get("carbs_g", 0)
        daily_stats[date_key]["fat_g"] += total.get("fat_g", 0)
        daily_stats[date_key]["meals_count"] += 1

    for key in daily_stats:
        for nutrient in ["calories", "protein_g", "carbs_g", "fat_g"]:
            daily_stats[key][nutrient] = round(daily_stats[key][nutrient], 1)

    user = await _db.users.find_one({"id": user_id}, {"_id": 0, "profile": 1})
    calorie_target = user.get("profile", {}).get("calorie_target", 2000)

    today_key = now.strftime("%Y-%m-%d")
    today_stats = daily_stats.get(today_key, {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals_count": 0})

    # Calculate streak (days within calorie target)
    streak = 0
    check_date = now
    for _ in range(30):
        dk = check_date.strftime("%Y-%m-%d")
        ds = daily_stats.get(dk)
        if ds and 0 < ds["calories"] <= calorie_target * 1.1:
            streak += 1
            check_date -= __import__('datetime').timedelta(days=1)
        else:
            break

    return {
        "period": period,
        "calorie_target": calorie_target,
        "today": today_stats,
        "daily_stats": [{"date": k, **v} for k, v in sorted(daily_stats.items())],
        "streak": streak,
        "total_meals": len(meals),
        "recent_meals": meals[:5]
    }


@router.post("/meal-plan")
async def create_meal_plan(req: MealPlanRequest, request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    from services.ai_provider import generate_meal_plan

    current = await get_current_user(request)
    user_id = current["user_id"]

    quota = await check_quota(user_id, "meal_plan")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail=f"Limite de planos alimentares atingido. Tente novamente no próximo período.")

    user = await _db.users.find_one({"id": user_id}, {"_id": 0})
    profile = user.get("profile", {})
    
    if not profile.get("weight") or not profile.get("height"):
        raise HTTPException(status_code=400, detail="Complete seu perfil (peso, altura, etc.) antes de gerar um plano alimentar.")

    from services.nutrition_db import calculate_calorie_target
    calorie_target = calculate_calorie_target(
        age=profile.get("age", 30),
        weight=profile.get("weight", 70),
        height=profile.get("height", 170),
        gender=profile.get("gender", "male"),
        activity_level=profile.get("activity_level", "moderate"),
        goal=profile.get("goal", "maintain")
    )

    plan_profile = {
        "age": profile.get("age", 30),
        "weight": profile.get("weight", 70),
        "height": profile.get("height", 170),
        "goal": profile.get("goal", "maintain"),
        "activity_level": profile.get("activity_level", "moderate"),
        "restrictions": ", ".join(profile.get("restrictions", [])) or "nenhuma",
        "calorie_target": calorie_target
    }

    ai_plan = await generate_meal_plan(plan_profile)
    
    plan_id = str(uuid.uuid4())
    plan = {
        "id": plan_id,
        "user_id": user_id,
        "plan_data": ai_plan,
        "calorie_target": calorie_target,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.meal_plans.insert_one(plan)
    await increment_quota(user_id, "meal_plan")

    return {"plan_id": plan_id, "plan": ai_plan, "calorie_target": calorie_target}


@router.get("/meal-plan")
async def get_meal_plan(request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    plan = await _db.meal_plans.find_one(
        {"user_id": current["user_id"]},
        {"_id": 0}
    )
    if not plan:
        return {"plan": None}
    # Sort descending and get latest
    plans = await _db.meal_plans.find(
        {"user_id": current["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(1).to_list(1)
    
    return plans[0] if plans else {"plan": None}


@router.get("/foods/search")
async def search_foods(q: str, limit: int = 10):
    from services.nutrition_db import search_food
    results = await search_food(q, limit)
    return {"foods": results, "total": len(results)}
