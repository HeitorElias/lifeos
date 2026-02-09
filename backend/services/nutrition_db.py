import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import re

load_dotenv()
logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


async def search_food(query: str, limit: int = 10) -> list:
    """Search foods by name in Portuguese or English."""
    query_lower = query.lower().strip()
    regex = re.compile(re.escape(query_lower), re.IGNORECASE)
    results = await _db.foods.find(
        {"$or": [
            {"name_pt": regex},
            {"name_en": regex},
            {"keywords": regex}
        ]},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    return results


async def find_food_by_name(name: str) -> dict:
    """Find a single food by name, trying Portuguese then English."""
    name_lower = name.lower().strip()
    # Try exact match first
    food = await _db.foods.find_one(
        {"$or": [
            {"name_pt": re.compile(f"^{re.escape(name_lower)}$", re.IGNORECASE)},
            {"name_en": re.compile(f"^{re.escape(name_lower)}$", re.IGNORECASE)}
        ]},
        {"_id": 0}
    )
    if food:
        return food
    # Try partial match
    regex = re.compile(re.escape(name_lower), re.IGNORECASE)
    food = await _db.foods.find_one(
        {"$or": [
            {"name_pt": regex},
            {"name_en": regex},
            {"keywords": regex}
        ]},
        {"_id": 0}
    )
    return food


def calculate_nutrients(food: dict, grams: float) -> dict:
    """Calculate nutrients for a given portion size based on per_100g data."""
    per_100g = food.get("per_100g", {})
    factor = grams / 100.0
    return {
        "calories": round(per_100g.get("calories", 0) * factor, 1),
        "protein_g": round(per_100g.get("protein", 0) * factor, 1),
        "carbs_g": round(per_100g.get("carbs", 0) * factor, 1),
        "fat_g": round(per_100g.get("fat", 0) * factor, 1),
        "fiber_g": round(per_100g.get("fiber", 0) * factor, 1),
        "sodium_mg": round(per_100g.get("sodium", 0) * factor, 1),
    }


async def calculate_meal_nutrients(items: list) -> dict:
    """Calculate total nutrients for a list of food items from AI detection."""
    meal_items = []
    total = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0, "sodium_mg": 0}
    
    for item in items:
        food_name = item.get("name", "")
        grams = item.get("estimated_grams", 100)
        confidence = item.get("confidence", 0.5)
        
        food = await find_food_by_name(food_name)
        
        if food:
            nutrients = calculate_nutrients(food, grams)
            meal_item = {
                "food_name": food_name,
                "food_name_matched": food.get("name_pt", food_name),
                "grams": grams,
                "confidence": confidence,
                "matched": True,
                "source": food.get("source", "TACO/USDA"),
                "nutrients": nutrients
            }
            for key in total:
                total[key] += nutrients.get(key, 0)
        else:
            meal_item = {
                "food_name": food_name,
                "food_name_matched": None,
                "grams": grams,
                "confidence": confidence,
                "matched": False,
                "source": None,
                "nutrients": None,
                "needs_confirmation": True
            }
        meal_items.append(meal_item)
    
    # Round totals
    for key in total:
        total[key] = round(total[key], 1)
    
    return {"items": meal_items, "total": total}


def calculate_calorie_target(age: int, weight: float, height: float, gender: str, activity_level: str, goal: str) -> int:
    """Calculate daily calorie target using Mifflin-St Jeor equation."""
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    tdee = bmr * activity_factors.get(activity_level, 1.55)
    
    goal_adjustments = {
        "lose_weight": -500,
        "lose_weight_fast": -750,
        "maintain": 0,
        "gain_muscle": 300,
        "gain_weight": 500
    }
    target = tdee + goal_adjustments.get(goal, 0)
    return max(1200, round(target))
