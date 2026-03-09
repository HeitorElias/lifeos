from __future__ import annotations

import json
from typing import Any

from services.ai_provider import process_finance_message
from services.transaction_sanitizer import transaction_sanitizer


class FinanceAIService:
    async def generate_insights(
        self,
        message: str,
        manual_expenses: list[dict[str, Any]],
        bank_transactions: list[dict[str, Any]],
        user_preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = transaction_sanitizer.build_insight_context(
            manual_expenses,
            bank_transactions,
            user_preferences=user_preferences,
        )
        context_json = json.dumps(context, ensure_ascii=False)
        return await process_finance_message(message, context_json)


finance_ai_service = FinanceAIService()
