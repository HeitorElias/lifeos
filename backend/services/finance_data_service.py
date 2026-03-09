from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class FinanceDataService:
    def __init__(self, db):
        self.db = db

    async def get_monthly_expenses(self, user_id: str, month: str) -> list[dict[str, Any]]:
        return await self.db.expenses.find(
            {"user_id": user_id, "date": {"$regex": f"^{month}"}},
            {"_id": 0},
        ).to_list(2000)

    async def get_monthly_bank_transactions(self, user_id: str, month: str) -> list[dict[str, Any]]:
        return await self.db.bank_transactions.find(
            {"user_id": user_id, "date": {"$regex": f"^{month}"}, "pending": {"$ne": True}},
            {"_id": 0},
        ).to_list(4000)

    async def build_dashboard(self, user_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        current_month = now.strftime("%Y-%m")
        prev_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        manual_current = await self.get_monthly_expenses(user_id, current_month)
        bank_current = await self.get_monthly_bank_transactions(user_id, current_month)
        manual_prev = await self.get_monthly_expenses(user_id, prev_month)
        bank_prev = await self.get_monthly_bank_transactions(user_id, prev_month)

        total_manual_current = sum(_to_float(row.get("amount")) for row in manual_current)
        total_bank_current = sum(_to_float(row.get("amount")) for row in bank_current)
        total_current = total_manual_current + total_bank_current

        total_prev = sum(_to_float(row.get("amount")) for row in manual_prev) + sum(
            _to_float(row.get("amount")) for row in bank_prev
        )

        categories = defaultdict(float)
        for row in manual_current:
            categories[row.get("category", "Outros")] += _to_float(row.get("amount"))
        for row in bank_current:
            cat = (row.get("category") or ["Outros"])[0]
            categories[cat] += _to_float(row.get("amount"))

        pending_bills = await self.db.bills.find(
            {"user_id": user_id, "status": "pending"}, {"_id": 0}
        ).sort("due_date", 1).to_list(50)

        return {
            "current_month": current_month,
            "total_expenses": round(total_current, 2),
            "manual_expenses_total": round(total_manual_current, 2),
            "bank_expenses_total": round(total_bank_current, 2),
            "prev_month_total": round(total_prev, 2),
            "difference": round(total_current - total_prev, 2),
            "categories": [
                {"name": key, "amount": round(value, 2)}
                for key, value in sorted(categories.items(), key=lambda x: -x[1])
            ],
            "pending_bills": pending_bills,
            "total_pending_bills": round(sum(_to_float(b.get("amount")) for b in pending_bills), 2),
            "expenses_count": len(manual_current) + len(bank_current),
            "sources": {
                "manual_expenses_count": len(manual_current),
                "bank_transactions_count": len(bank_current),
            },
        }
