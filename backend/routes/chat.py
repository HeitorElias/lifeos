from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/chat", tags=["Chat"])

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


class ChatMessage(BaseModel):
    message: str
    module: str = "general"  # nutrition, agenda, finance, general


@router.post("/message")
async def send_message(req: ChatMessage, request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    user_id = current["user_id"]

    # Save user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "role": "user",
        "content": req.message,
        "module": req.module,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.chat_messages.insert_one(user_msg)

    response_data = {}
    response_text = ""

    try:
        if req.module == "agenda":
            from services.ai_provider import process_agenda_message
            from services.quota import check_quota, increment_quota

            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            ai_result = await process_agenda_message(req.message, today)
            response_text = ai_result.get("response_text", "Entendi sua solicitação sobre agenda.")
            response_data = ai_result

            intent = ai_result.get("intent", "general_query")
            payload = ai_result.get("payload", {})

            if intent == "create_event" and payload.get("title"):
                quota = await check_quota(user_id, "agenda_actions")
                if quota["allowed"]:
                    event_id = str(uuid.uuid4())
                    event = {
                        "id": event_id,
                        "user_id": user_id,
                        "title": payload.get("title", ""),
                        "date": payload.get("date", today),
                        "time": payload.get("time", "09:00"),
                        "end_time": payload.get("end_time"),
                        "location": payload.get("location"),
                        "notes": payload.get("notes"),
                        "status": "active",
                        "reminder_email": True,
                        "reminder_whatsapp": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    await _db.events.insert_one(event)
                    await increment_quota(user_id, "agenda_actions")
                    response_data["event_created"] = event_id
                    response_text += f"\n\nEvento '{payload['title']}' criado com sucesso!"
                else:
                    response_text += "\n\nVocê atingiu o limite de ações na agenda. Faça upgrade do plano."

            elif intent == "list_events":
                events = await _db.events.find(
                    {"user_id": user_id, "status": "active", "date": {"$gte": today}},
                    {"_id": 0}
                ).sort([("date", 1), ("time", 1)]).limit(10).to_list(10)
                response_data["events"] = events
                if events:
                    events_text = "\n".join([f"- {e['title']} em {e['date']} às {e['time']}" for e in events])
                    response_text = f"Seus próximos compromissos:\n{events_text}"
                else:
                    response_text = "Você não tem compromissos agendados."

        elif req.module == "finance":
            from services.finance_ai_service import finance_ai_service

            now = datetime.now(timezone.utc)
            current_month = now.strftime("%Y-%m")
            prev_month = (now.replace(day=1) - __import__('datetime').timedelta(days=1)).strftime("%Y-%m")

            manual_expenses = await _db.expenses.find(
                {"user_id": user_id, "date": {"$regex": f"^{current_month}|^{prev_month}"}},
                {"_id": 0}
            ).to_list(500)
            bank_transactions = await _db.bank_transactions.find(
                {"user_id": user_id, "date": {"$regex": f"^{current_month}|^{prev_month}"}, "pending": {"$ne": True}},
                {"_id": 0}
            ).to_list(1000)

            user = await _db.users.find_one({"id": user_id}, {"_id": 0, "profile": 1})
            user_preferences = (user or {}).get("profile", {}).get("finance_preferences", {})

            ai_result = await finance_ai_service.generate_insights(
                req.message,
                manual_expenses,
                bank_transactions,
                user_preferences=user_preferences,
            )
            response_text = ai_result.get("response_text", "Entendi sua solicitação financeira.")
            response_data = ai_result

        elif req.module == "nutrition":
            from services.ai_provider import analyze_food_text
            from services.nutrition_db import calculate_meal_nutrients

            ai_result = await analyze_food_text(req.message)
            items = ai_result.get("items", [])
            if items:
                nutrition = await calculate_meal_nutrients(items)
                total = nutrition["total"]
                response_text = f"Registrei sua refeição:\n"
                for item in nutrition["items"]:
                    name = item.get("food_name_matched") or item.get("food_name")
                    cals = item.get("nutrients", {}).get("calories", 0) if item.get("nutrients") else "?"
                    response_text += f"- {name} ({item['grams']}g): {cals} kcal\n"
                response_text += f"\nTotal: {total['calories']} kcal | P: {total['protein_g']}g | C: {total['carbs_g']}g | G: {total['fat_g']}g"
                response_data = {"nutrition": nutrition, "ai_result": ai_result}

                meal_id = str(uuid.uuid4())
                meal = {
                    "id": meal_id,
                    "user_id": user_id,
                    "type": "text",
                    "meal_type": ai_result.get("meal_type", "refeição"),
                    "original_text": req.message,
                    "items": nutrition["items"],
                    "total_nutrients": nutrition["total"],
                    "ai_raw_response": ai_result,
                    "has_photo": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await _db.meals.insert_one(meal)
                response_data["meal_id"] = meal_id
            else:
                response_text = "Não consegui identificar alimentos na sua mensagem. Tente descrever sua refeição com mais detalhes."
                response_data = ai_result

        else:
            response_text = "Posso te ajudar com Nutrição, Agenda ou Finanças. Sobre o que gostaria de conversar?"
            response_data = {"hint": "Escolha um módulo: nutrition, agenda ou finance"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        response_text = f"Desculpe, tive um problema ao processar sua mensagem. Tente novamente."
        response_data = {"error": str(e)}

    # Save assistant message
    assistant_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "role": "assistant",
        "content": response_text,
        "module": req.module,
        "data": response_data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.chat_messages.insert_one(assistant_msg)

    return {
        "message": response_text,
        "data": response_data,
        "module": req.module
    }


@router.get("/history")
async def get_history(request: Request, module: Optional[str] = None, limit: int = 50):
    from middleware.auth import get_current_user
    current = await get_current_user(request)

    query = {"user_id": current["user_id"]}
    if module:
        query["module"] = module

    messages = await _db.chat_messages.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    messages.reverse()
    return {"messages": messages, "total": len(messages)}
