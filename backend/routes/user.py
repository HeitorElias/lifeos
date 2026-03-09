from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/user", tags=["User"])

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


class FinancePreferencesUpdate(BaseModel):
    monthly_savings_goal: Optional[float] = None
    risk_profile: Optional[str] = None
    priority_categories: Optional[List[str]] = None
    report_style: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    restrictions: Optional[List[str]] = None
    finance_preferences: Optional[FinancePreferencesUpdate] = None


class OnboardingRequest(BaseModel):
    age: int
    weight: float
    height: float
    gender: str
    activity_level: str
    goal: str
    restrictions: List[str] = []


@router.get("/profile")
async def get_profile(request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    user = await _db.users.find_one({"id": current["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.put("/profile")
async def update_profile(req: ProfileUpdate, request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)

    update_data = {}
    if req.name:
        update_data["name"] = req.name

    payload = req.model_dump(exclude_none=True)
    profile_fields = {k: v for k, v in payload.items() if k != "name"}
    if profile_fields:
        for k, v in profile_fields.items():
            if k == "finance_preferences" and isinstance(v, dict):
                update_data["profile.finance_preferences"] = v
            else:
                update_data[f"profile.{k}"] = v

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.users.update_one({"id": current["user_id"]}, {"$set": update_data})

    user = await _db.users.find_one({"id": current["user_id"]}, {"_id": 0, "password_hash": 0})
    return user


@router.post("/onboarding")
async def complete_onboarding(req: OnboardingRequest, request: Request):
    from middleware.auth import get_current_user
    from services.nutrition_db import calculate_calorie_target
    current = await get_current_user(request)

    calorie_target = calculate_calorie_target(
        age=req.age, weight=req.weight, height=req.height,
        gender=req.gender, activity_level=req.activity_level, goal=req.goal
    )

    profile = {
        "age": req.age,
        "weight": req.weight,
        "height": req.height,
        "gender": req.gender,
        "activity_level": req.activity_level,
        "goal": req.goal,
        "restrictions": req.restrictions,
        "calorie_target": calorie_target
    }

    await _db.users.update_one(
        {"id": current["user_id"]},
        {"$set": {
            "profile": profile,
            "onboarding_complete": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    return {"message": "Onboarding completo!", "calorie_target": calorie_target, "profile": profile}


@router.get("/quota")
async def get_quota(request: Request):
    from middleware.auth import get_current_user
    from services.quota import get_all_quotas
    current = await get_current_user(request)
    return await get_all_quotas(current["user_id"])


@router.get("/plans")
async def get_plans():
    plans = await _db.plans.find({}, {"_id": 0}).to_list(10)
    return {"plans": plans}


@router.post("/simulate-upgrade")
async def simulate_upgrade(request: Request):
    """Admin endpoint to simulate plan upgrade."""
    from middleware.auth import get_current_user
    current = await get_current_user(request)

    body = await request.json()
    plan_id = body.get("plan_id", "pro")

    plan = await _db.plans.find_one({"id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    await _db.users.update_one(
        {"id": current["user_id"]},
        {"$set": {"plan_id": plan_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"message": f"Upgrade para {plan['name']} simulado com sucesso!", "plan_id": plan_id}
