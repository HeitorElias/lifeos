import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


async def get_user_plan(user_id: str) -> dict:
    """Get user's current plan with quotas."""
    user = await _db.users.find_one({"id": user_id}, {"_id": 0, "plan_id": 1})
    plan_id = user.get("plan_id", "free") if user else "free"
    plan = await _db.plans.find_one({"id": plan_id}, {"_id": 0})
    return plan or await _db.plans.find_one({"id": "free"}, {"_id": 0})


async def check_quota(user_id: str, feature: str) -> dict:
    """Check if user has quota remaining for a feature. Returns usage info."""
    plan = await get_user_plan(user_id)
    quota_config = plan.get("quotas", {}).get(feature)
    
    if not quota_config:
        return {"allowed": False, "reason": "Feature não encontrada no plano"}
    
    limit = quota_config["limit"]
    if limit == -1:
        return {"allowed": True, "used": 0, "limit": -1, "remaining": -1}
    
    period = quota_config["period"]
    now = datetime.now(timezone.utc)
    
    if period == "monthly":
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "weekly":
        period_start = now - timedelta(days=now.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "daily":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    usage = await _db.quota_usage.find_one(
        {"user_id": user_id, "feature": feature, "period_start": period_start.isoformat()},
        {"_id": 0}
    )
    used = usage.get("count", 0) if usage else 0
    remaining = limit - used
    
    return {
        "allowed": remaining > 0,
        "used": used,
        "limit": limit,
        "remaining": max(0, remaining),
        "period": period,
        "plan_name": plan.get("name", "Free")
    }


async def increment_quota(user_id: str, feature: str) -> bool:
    """Increment quota usage for a feature."""
    plan = await get_user_plan(user_id)
    quota_config = plan.get("quotas", {}).get(feature)
    
    if not quota_config:
        return False
    
    if quota_config["limit"] == -1:
        return True
    
    period = quota_config["period"]
    now = datetime.now(timezone.utc)
    
    if period == "monthly":
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "weekly":
        period_start = now - timedelta(days=now.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "daily":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    await _db.quota_usage.update_one(
        {"user_id": user_id, "feature": feature, "period_start": period_start.isoformat()},
        {"$inc": {"count": 1}, "$set": {"updated_at": now.isoformat()}},
        upsert=True
    )
    return True


async def get_all_quotas(user_id: str) -> dict:
    """Get all quota usage for a user."""
    plan = await get_user_plan(user_id)
    quotas = plan.get("quotas", {})
    result = {}
    
    for feature, config in quotas.items():
        usage = await check_quota(user_id, feature)
        result[feature] = {
            "used": usage["used"],
            "limit": config["limit"],
            "remaining": usage["remaining"],
            "period": config["period"],
            "unlimited": config["limit"] == -1
        }
    
    return {"plan": plan.get("name", "Free"), "plan_id": plan.get("id", "free"), "quotas": result}
