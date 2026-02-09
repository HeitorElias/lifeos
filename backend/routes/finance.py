from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/finance", tags=["Finance"])

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]


class BillCreate(BaseModel):
    name: str
    amount: float
    due_date: str  # YYYY-MM-DD
    category: str
    recurrence: str = "once"  # once, monthly, weekly
    notes: Optional[str] = None


class BillUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(BaseModel):
    amount: float
    date: str  # YYYY-MM-DD
    category: str
    description: str


@router.get("/bills")
async def get_bills(request: Request, status: Optional[str] = None):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    query = {"user_id": current["user_id"]}
    if status:
        query["status"] = status
    
    bills = await _db.bills.find(query, {"_id": 0}).sort("due_date", 1).to_list(100)
    return {"bills": bills, "total": len(bills)}


@router.post("/bills")
async def create_bill(req: BillCreate, request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    user_id = current["user_id"]
    
    bill_id = str(uuid.uuid4())
    bill = {
        "id": bill_id,
        "user_id": user_id,
        "name": req.name,
        "amount": req.amount,
        "due_date": req.due_date,
        "category": req.category,
        "recurrence": req.recurrence,
        "notes": req.notes,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.bills.insert_one(bill)
    
    # Create payment reminders (mocked for MVP)
    for days_before in [3, 1, 0]:
        reminder = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "bill_id": bill_id,
            "type": "bill_reminder",
            "days_before": days_before,
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await _db.reminders.insert_one(reminder)
    
    return {k: v for k, v in bill.items() if k != "_id"}


@router.put("/bills/{bill_id}")
async def update_bill(bill_id: str, req: BillUpdate, request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    existing = await _db.bills.find_one({"id": bill_id, "user_id": current["user_id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if req.status == "paid":
        # Cancel pending reminders
        await _db.reminders.update_many(
            {"bill_id": bill_id, "status": "scheduled"},
            {"$set": {"status": "cancelled"}}
        )
    
    await _db.bills.update_one({"id": bill_id}, {"$set": update_data})
    updated = await _db.bills.find_one({"id": bill_id}, {"_id": 0})
    return updated


@router.delete("/bills/{bill_id}")
async def delete_bill(bill_id: str, request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    result = await _db.bills.delete_one({"id": bill_id, "user_id": current["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    await _db.reminders.delete_many({"bill_id": bill_id})
    return {"message": "Conta removida"}


@router.get("/expenses")
async def get_expenses(request: Request, month: Optional[str] = None, limit: int = 50):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    query = {"user_id": current["user_id"]}
    if month:
        query["date"] = {"$regex": f"^{month}"}
    
    expenses = await _db.expenses.find(query, {"_id": 0}).sort("date", -1).to_list(limit)
    return {"expenses": expenses, "total": len(expenses)}


@router.post("/expenses")
async def create_expense(req: ExpenseCreate, request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    
    expense_id = str(uuid.uuid4())
    expense = {
        "id": expense_id,
        "user_id": current["user_id"],
        "amount": req.amount,
        "date": req.date,
        "category": req.category,
        "description": req.description,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.expenses.insert_one(expense)
    return {k: v for k, v in expense.items() if k != "_id"}


@router.get("/dashboard")
async def get_finance_dashboard(request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    user_id = current["user_id"]
    
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    prev_month_dt = now.replace(day=1) - __import__('datetime').timedelta(days=1)
    prev_month = prev_month_dt.strftime("%Y-%m")
    
    # Current month expenses
    current_expenses = await _db.expenses.find(
        {"user_id": user_id, "date": {"$regex": f"^{current_month}"}},
        {"_id": 0}
    ).to_list(1000)
    
    # Previous month expenses
    prev_expenses = await _db.expenses.find(
        {"user_id": user_id, "date": {"$regex": f"^{prev_month}"}},
        {"_id": 0}
    ).to_list(1000)
    
    # Category breakdown
    categories = {}
    total_current = 0
    for exp in current_expenses:
        cat = exp.get("category", "Outros")
        categories[cat] = categories.get(cat, 0) + exp.get("amount", 0)
        total_current += exp.get("amount", 0)
    
    total_prev = sum(e.get("amount", 0) for e in prev_expenses)
    
    # Pending bills
    pending_bills = await _db.bills.find(
        {"user_id": user_id, "status": "pending"},
        {"_id": 0}
    ).sort("due_date", 1).to_list(20)
    
    total_pending = sum(b.get("amount", 0) for b in pending_bills)
    
    return {
        "current_month": current_month,
        "total_expenses": round(total_current, 2),
        "prev_month_total": round(total_prev, 2),
        "difference": round(total_current - total_prev, 2),
        "categories": [{"name": k, "amount": round(v, 2)} for k, v in sorted(categories.items(), key=lambda x: -x[1])],
        "pending_bills": pending_bills,
        "total_pending_bills": round(total_pending, 2),
        "expenses_count": len(current_expenses)
    }


@router.post("/analyze")
async def analyze_finances(request: Request):
    from middleware.auth import get_current_user
    from services.quota import check_quota, increment_quota
    from services.ai_provider import process_finance_message
    
    current = await get_current_user(request)
    user_id = current["user_id"]
    
    quota = await check_quota(user_id, "finance_analysis")
    if not quota["allowed"]:
        raise HTTPException(status_code=429, detail="Limite de análises financeiras atingido.")
    
    # Build finance context
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    
    expenses = await _db.expenses.find(
        {"user_id": user_id, "date": {"$regex": f"^{current_month}"}},
        {"_id": 0}
    ).to_list(200)
    
    categories = {}
    for exp in expenses:
        cat = exp.get("category", "Outros")
        categories[cat] = categories.get(cat, 0) + exp.get("amount", 0)
    
    context = f"Total gasto em {current_month}: R$ {sum(e.get('amount', 0) for e in expenses):.2f}\n"
    context += "Gastos por categoria:\n"
    for cat, amount in sorted(categories.items(), key=lambda x: -x[1]):
        context += f"- {cat}: R$ {amount:.2f}\n"
    
    result = await process_finance_message("Analise meus gastos e sugira onde posso economizar.", context)
    await increment_quota(user_id, "finance_analysis")
    
    await _db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": "finance_analysis",
        "details": {"context": context[:500]},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return result
