from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

from middleware.auth import get_current_user
from models.plaid import PlaidExchangeRequest, PlaidLinkTokenRequest, PlaidSyncRequest, PlaidWebhookPayload
from services.crypto_service import crypto_service
from services.plaid_service import PlaidAPIError, plaid_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/plaid", tags=["Plaid"])

mongo_url = os.environ["MONGO_URL"]
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ["DB_NAME"]]




def _allowed_paid_plans() -> set[str]:
    return {plan.strip() for plan in os.environ.get("PLAID_ALLOWED_PLANS", "pro,premium").split(",") if plan.strip()}


async def _ensure_paid_plan_access(user_id: str) -> None:
    user = await _db.users.find_one({"id": user_id}, {"_id": 0, "plan_id": 1})
    plan_id = (user or {}).get("plan_id", "free")
    if plan_id not in _allowed_paid_plans():
        raise HTTPException(
            status_code=403,
            detail="Integração bancária via Plaid disponível apenas para planos pagos.",
        )

@router.on_event("startup")
async def setup_indexes() -> None:
    await _db.plaid_items.create_index([("user_id", 1), ("item_id", 1)], unique=True)
    await _db.bank_transactions.create_index([("user_id", 1), ("transaction_id", 1)], unique=True)


@router.post("/link-token")
async def create_link_token(req: PlaidLinkTokenRequest, request: Request):
    current = await get_current_user(request)
    await _ensure_paid_plan_access(current["user_id"])
    if not plaid_service.configured():
        raise HTTPException(status_code=503, detail="Plaid não configurado no ambiente")

    try:
        response = await plaid_service.create_link_token(
            user_id=current["user_id"],
            client_name=req.client_name,
            language=req.language,
        )
    except PlaidAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao criar link token: {exc}") from exc

    return {"link_token": response.get("link_token"), "expiration": response.get("expiration")}


@router.post("/exchange")
async def exchange_public_token(req: PlaidExchangeRequest, request: Request):
    current = await get_current_user(request)
    await _ensure_paid_plan_access(current["user_id"])
    now = datetime.now(timezone.utc)

    try:
        exchange_data = await plaid_service.exchange_public_token(req.public_token)
    except PlaidAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao trocar public_token: {exc}") from exc

    item_id = exchange_data.get("item_id")
    access_token = exchange_data.get("access_token")
    if not item_id or not access_token:
        raise HTTPException(status_code=502, detail="Resposta inválida da Plaid no exchange")

    encrypted = crypto_service.encrypt(access_token)
    await _db.plaid_items.update_one(
        {"user_id": current["user_id"], "item_id": item_id},
        {
            "$set": {
                "access_token_enc": encrypted.value,
                "institution_id": req.institution_id,
                "updated_at": now.isoformat(),
            },
            "$setOnInsert": {
                "user_id": current["user_id"],
                "item_id": item_id,
                "cursor": None,
                "created_at": now.isoformat(),
            },
        },
        upsert=True,
    )

    return {"item_id": item_id, "status": "connected"}


@router.post("/sync")
async def sync_transactions(req: PlaidSyncRequest, request: Request):
    current = await get_current_user(request)
    await _ensure_paid_plan_access(current["user_id"])
    items = await _db.plaid_items.find({"user_id": current["user_id"]}, {"_id": 0}).to_list(100)
    if not items:
        return {"items_synced": 0, "transactions_upserted": 0, "transactions_removed": 0}

    upserts = 0
    removals = 0

    for item in items:
        access_token = crypto_service.decrypt(item["access_token_enc"])
        cursor = None if req.full_refresh else item.get("cursor")
        sync_response = await plaid_service.sync_transactions(access_token=access_token, cursor=cursor)

        now = datetime.now(timezone.utc).isoformat()
        operations = []
        for transaction in sync_response.get("added", []) + sync_response.get("modified", []):
            transaction_id = transaction.get("transaction_id")
            if not transaction_id:
                continue

            operations.append(
                UpdateOne(
                    {"user_id": current["user_id"], "transaction_id": transaction_id},
                    {
                        "$set": {
                            "user_id": current["user_id"],
                            "item_id": item["item_id"],
                            "account_id": transaction.get("account_id"),
                            "transaction_id": transaction_id,
                            "amount": transaction.get("amount", 0),
                            "iso_currency_code": transaction.get("iso_currency_code"),
                            "date": transaction.get("date"),
                            "name": transaction.get("name"),
                            "merchant_name": transaction.get("merchant_name"),
                            "pending": transaction.get("pending", False),
                            "category": transaction.get("category") or [],
                            "payment_channel": transaction.get("payment_channel"),
                            "raw": transaction,
                            "updated_at": now,
                        },
                        "$setOnInsert": {"created_at": now},
                    },
                    upsert=True,
                )
            )

        removed_ids = [item.get("transaction_id") for item in sync_response.get("removed", []) if item.get("transaction_id")]
        if operations:
            bulk_result = await _db.bank_transactions.bulk_write(operations, ordered=False)
            upserts += bulk_result.upserted_count + bulk_result.modified_count

        if removed_ids:
            removed_result = await _db.bank_transactions.delete_many(
                {"user_id": current["user_id"], "transaction_id": {"$in": removed_ids}}
            )
            removals += removed_result.deleted_count

        await _db.plaid_items.update_one(
            {"user_id": current["user_id"], "item_id": item["item_id"]},
            {"$set": {"cursor": sync_response.get("next_cursor"), "updated_at": now}},
        )

    return {
        "items_synced": len(items),
        "transactions_upserted": upserts,
        "transactions_removed": removals,
    }


@router.post("/webhook")
async def plaid_webhook(payload: PlaidWebhookPayload):
    now = datetime.now(timezone.utc).isoformat()
    await _db.plaid_webhook_events.insert_one({**payload.model_dump(), "received_at": now})
    logger.info("Plaid webhook received type=%s code=%s", payload.webhook_type, payload.webhook_code)
    return {"status": "accepted"}
