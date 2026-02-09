from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/agenda", tags=["Agenda"])

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


class EventCreate(BaseModel):
    title: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    end_time: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    reminder_email: bool = True
    reminder_whatsapp: bool = False


class EventUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


@router.get("/events")
async def get_events(request: Request, date: Optional[str] = None, period: str = "week"):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    query = {"user_id": current["user_id"], "status": {"$ne": "cancelled"}}
    
    if date:
        query["date"] = date
    elif period == "day":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["date"] = today
    elif period == "week":
        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-%d")
        end = (now + __import__('datetime').timedelta(days=7)).strftime("%Y-%m-%d")
        query["date"] = {"$gte": start, "$lte": end}
    elif period == "month":
        now = datetime.now(timezone.utc)
        start = now.replace(day=1).strftime("%Y-%m-%d")
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1)
        end = end_date.strftime("%Y-%m-%d")
        query["date"] = {"$gte": start, "$lt": end}
    
    events = await _db.events.find(query, {"_id": 0}).sort([("date", 1), ("time", 1)]).to_list(100)
    return {"events": events, "total": len(events)}


@router.post("/events")
async def create_event(req: EventCreate, request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    
    current = await get_current_user(request)
    user_id = current["user_id"]
    
    quota = await check_quota(user_id, "agenda_actions")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail="Limite de ações na agenda atingido. Faça upgrade do plano.")
    
    event_id = str(uuid.uuid4())
    event = {
        "id": event_id,
        "user_id": user_id,
        "title": req.title,
        "date": req.date,
        "time": req.time,
        "end_time": req.end_time,
        "location": req.location,
        "notes": req.notes,
        "status": "active",
        "reminder_email": req.reminder_email,
        "reminder_whatsapp": req.reminder_whatsapp,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.events.insert_one(event)
    await increment_quota(user_id, "agenda_actions")
    
    # Create reminders (mocked for MVP - would use BullMQ/Celery in production)
    if req.reminder_email or req.reminder_whatsapp:
        reminder = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "event_id": event_id,
            "channels": [],
            "send_at_24h": f"{req.date}T{req.time}:00Z",
            "send_at_1h": f"{req.date}T{req.time}:00Z",
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if req.reminder_email:
            reminder["channels"].append("email")
        if req.reminder_whatsapp:
            reminder["channels"].append("whatsapp")
        await _db.reminders.insert_one(reminder)
    
    await _db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": "create_event",
        "details": {"event_id": event_id, "title": req.title},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {**event, "_id": None}


@router.put("/events/{event_id}")
async def update_event(event_id: str, req: EventUpdate, request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    
    current = await get_current_user(request)
    user_id = current["user_id"]
    
    quota = await check_quota(user_id, "agenda_actions")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail="Limite de ações na agenda atingido.")
    
    existing = await _db.events.find_one({"id": event_id, "user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await _db.events.update_one({"id": event_id}, {"$set": update_data})
    await increment_quota(user_id, "agenda_actions")
    
    updated = await _db.events.find_one({"id": event_id}, {"_id": 0})
    return updated


@router.delete("/events/{event_id}")
async def cancel_event(event_id: str, request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    
    current = await get_current_user(request)
    user_id = current["user_id"]
    
    quota = await check_quota(user_id, "agenda_actions")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail="Limite de ações na agenda atingido.")
    
    result = await _db.events.update_one(
        {"id": event_id, "user_id": user_id},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    await increment_quota(user_id, "agenda_actions")
    
    await _db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": "cancel_event",
        "details": {"event_id": event_id},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Evento cancelado", "event_id": event_id}
