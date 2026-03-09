from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from middleware.auth import get_current_user
from services.finance_ai_service import finance_ai_service
from services.finance_data_service import FinanceDataService
from services.quota import check_quota, increment_quota

router = APIRouter(prefix="/api/finance", tags=["Finance"])

mongo_url = os.environ["MONGO_URL"]
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ["DB_NAME"]]
finance_data_service = FinanceDataService(_db)


class BillCreate(BaseModel):
    name: str = Field(min_length=2)
    amount: float = Field(gt=0)
    due_date: str
    category: str
    recurrence: str = "once"
    notes: Optional[str] = None


class BillUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    due_date: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    date: str
    category: str
    description: str


class FinanceAnalyzeRequest(BaseModel):
    prompt: str = "Analise meus gastos e sugira onde posso economizar com um relatório completo."
    months_back: int = Field(default=2, ge=1, le=12)


@router.get("/bills")
async def get_bills(request: Request, status: Optional[str] = None):
    current = await get_current_user(request)
    query = {"user_id": current["user_id"]}
    if status:
        query["status"] = status
    bills = await _db.bills.find(query, {"_id": 0}).sort("due_date", 1).to_list(200)
    return {"bills": bills, "total": len(bills)}


@router.post("/bills")
async def create_bill(req: BillCreate, request: Request):
    current = await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    bill_id = str(uuid.uuid4())
    bill = {
        "id": bill_id,
        "user_id": current["user_id"],
        "name": req.name,
        "amount": req.amount,
        "due_date": req.due_date,
        "category": req.category,
        "recurrence": req.recurrence,
        "notes": req.notes,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    await _db.bills.insert_one(bill)

    reminders = [
        {
            "id": str(uuid.uuid4()),
            "user_id": current["user_id"],
            "bill_id": bill_id,
            "type": "bill_reminder",
            "days_before": days_before,
            "status": "scheduled",
            "created_at": now,
        }
        for days_before in [3, 1, 0]
    ]
    await _db.reminders.insert_many(reminders)
    return bill


@router.put("/bills/{bill_id}")
async def update_bill(bill_id: str, req: BillUpdate, request: Request):
    current = await get_current_user(request)
    existing = await _db.bills.find_one({"id": bill_id, "user_id": current["user_id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    if req.status == "paid":
        await _db.reminders.update_many(
            {"bill_id": bill_id, "status": "scheduled"},
            {"$set": {"status": "cancelled", "updated_at": update_data["updated_at"]}},
        )

    await _db.bills.update_one({"id": bill_id, "user_id": current["user_id"]}, {"$set": update_data})
    return await _db.bills.find_one({"id": bill_id, "user_id": current["user_id"]}, {"_id": 0})


@router.delete("/bills/{bill_id}")
async def delete_bill(bill_id: str, request: Request):
    current = await get_current_user(request)
    result = await _db.bills.delete_one({"id": bill_id, "user_id": current["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    await _db.reminders.delete_many({"bill_id": bill_id, "user_id": current["user_id"]})
    return {"message": "Conta removida"}


@router.get("/expenses")
async def get_expenses(request: Request, month: Optional[str] = None, limit: int = Query(default=50, ge=1, le=500)):
    current = await get_current_user(request)
    query = {"user_id": current["user_id"]}
    if month:
        query["date"] = {"$regex": f"^{month}"}
    expenses = await _db.expenses.find(query, {"_id": 0}).sort("date", -1).to_list(limit)
    return {"expenses": expenses, "total": len(expenses)}


@router.post("/expenses")
async def create_expense(req: ExpenseCreate, request: Request):
    current = await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    expense = {
        "id": str(uuid.uuid4()),
        "user_id": current["user_id"],
        "amount": req.amount,
        "date": req.date,
        "category": req.category,
        "description": req.description,
        "source": "manual",
        "created_at": now,
        "updated_at": now,
    }
    await _db.expenses.insert_one(expense)
    return expense


@router.get("/transactions")
async def get_bank_transactions(
    request: Request,
    month: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Read-only listing of synced bank transactions for paid users with connected accounts."""
    current = await get_current_user(request)
    query = {"user_id": current["user_id"]}
    if month:
        query["date"] = {"$regex": f"^{month}"}

    transactions = await _db.bank_transactions.find(query, {"_id": 0, "raw": 0}).sort("date", -1).to_list(limit)
    return {"transactions": transactions, "total": len(transactions)}


@router.get("/dashboard")
async def get_finance_dashboard(request: Request):
    current = await get_current_user(request)
    return await finance_data_service.build_dashboard(current["user_id"])


@router.post("/analyze")
async def analyze_finances(request: Request, payload: FinanceAnalyzeRequest):
    current = await get_current_user(request)
    user_id = current["user_id"]

    quota = await check_quota(user_id, "finance_analysis")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail="Limite de análises financeiras atingido.")

    now = datetime.now(timezone.utc)
    month_prefixes: list[str] = []
    cursor = now.replace(day=1)
    for _ in range(payload.months_back):
        month_prefixes.append(cursor.strftime("%Y-%m"))
        cursor = (cursor - __import__("datetime").timedelta(days=1)).replace(day=1)

    month_regex = "|".join(f"^{month}" for month in month_prefixes)

    manual_expenses = await _db.expenses.find(
        {"user_id": user_id, "date": {"$regex": month_regex}}, {"_id": 0}
    ).to_list(1000)
    bank_transactions = await _db.bank_transactions.find(
        {"user_id": user_id, "date": {"$regex": month_regex}, "pending": {"$ne": True}}, {"_id": 0}
    ).to_list(2000)

    user = await _db.users.find_one({"id": user_id}, {"_id": 0, "profile": 1})
    user_preferences = (user or {}).get("profile", {}).get("finance_preferences", {})

    result = await finance_ai_service.generate_insights(
        message=payload.prompt,
        manual_expenses=manual_expenses,
        bank_transactions=bank_transactions,
        user_preferences=user_preferences,
    )

    await increment_quota(user_id, "finance_analysis")
    await _db.audit_logs.insert_one(
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": "finance_analysis",
            "details": {
                "manual_expenses_count": len(manual_expenses),
                "bank_transactions_count": len(bank_transactions),
                "months_back": payload.months_back,
                "intent": result.get("intent"),
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return result
