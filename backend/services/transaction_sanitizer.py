from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any


class TransactionSanitizer:
    """Builds a privacy-safe AI context from raw financial records."""

    def _month_key(self, date_value: str) -> str:
        return date_value[:7] if date_value else "unknown"

    def build_insight_context(
        self,
        expenses: list[dict[str, Any]],
        bank_transactions: list[dict[str, Any]],
        user_preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        merged = []
        for expense in expenses:
            merged.append(
                {
                    "amount": float(expense.get("amount", 0)),
                    "category": expense.get("category", "Outros"),
                    "month": self._month_key(expense.get("date", "")),
                    "description": expense.get("description", "Gasto manual")[:60],
                }
            )
        for txn in bank_transactions:
            category = (txn.get("category") or ["Outros"])[0]
            merged.append(
                {
                    "amount": float(txn.get("amount", 0)),
                    "category": category,
                    "month": self._month_key(txn.get("date", "")),
                    "description": (txn.get("merchant_name") or txn.get("name") or "Transação bancária")[:60],
                }
            )

        by_category = defaultdict(float)
        by_month = defaultdict(float)
        description_totals = defaultdict(float)

        for row in merged:
            by_category[row["category"]] += row["amount"]
            by_month[row["month"]] += row["amount"]
            description_totals[row["description"]] += row["amount"]

        top_categories = sorted(by_category.items(), key=lambda item: item[1], reverse=True)[:8]
        top_spends = sorted(description_totals.items(), key=lambda item: item[1], reverse=True)[:8]
        average_ticket = (sum(row["amount"] for row in merged) / len(merged)) if merged else 0

        monthly_sorted = sorted(by_month.items(), key=lambda item: item[0])
        monthly_variation = []
        for index in range(1, len(monthly_sorted)):
            prev_month, prev_total = monthly_sorted[index - 1]
            curr_month, curr_total = monthly_sorted[index]
            variation = curr_total - prev_total
            monthly_variation.append(
                {
                    "from": prev_month,
                    "to": curr_month,
                    "delta": round(variation, 2),
                    "delta_percent": round((variation / prev_total * 100) if prev_total else 0, 2),
                }
            )

        recurring_candidates = [
            name for name, amount in description_totals.items() if amount > 0 and sum(1 for row in merged if row["description"] == name) >= 2
        ][:6]

        preferences = {
            "monthly_savings_goal": user_preferences.get("monthly_savings_goal") if user_preferences else None,
            "risk_profile": user_preferences.get("risk_profile") if user_preferences else None,
            "priority_categories": user_preferences.get("priority_categories") if user_preferences else [],
            "report_style": user_preferences.get("report_style", "executive") if user_preferences else "executive",
        }

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_spend": round(sum(row["amount"] for row in merged), 2),
            "transaction_count": len(merged),
            "average_ticket": round(average_ticket, 2),
            "top_categories": [{"name": name, "amount": round(value, 2)} for name, value in top_categories],
            "top_spends": [{"name": name, "amount": round(value, 2)} for name, value in top_spends],
            "monthly_variation": monthly_variation,
            "subscription_candidates": recurring_candidates,
            "high_impact_categories": [name for name, _ in top_categories[:3]],
            "user_preferences": preferences,
        }


transaction_sanitizer = TransactionSanitizer()
