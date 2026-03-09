from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PlaidLinkTokenRequest(BaseModel):
    client_name: str = Field(default="LifeOS")
    language: str = Field(default="pt")


class PlaidExchangeRequest(BaseModel):
    public_token: str = Field(min_length=10)
    institution_id: Optional[str] = None


class PlaidSyncRequest(BaseModel):
    full_refresh: bool = False


class PlaidWebhookPayload(BaseModel):
    webhook_type: str
    webhook_code: str
    item_id: Optional[str] = None
    error: Optional[dict[str, Any]] = None


class PlaidItemRecord(BaseModel):
    user_id: str
    item_id: str
    access_token_enc: str
    institution_id: Optional[str] = None
    cursor: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BankTransactionRecord(BaseModel):
    user_id: str
    item_id: str
    account_id: str
    transaction_id: str
    amount: float
    iso_currency_code: Optional[str] = None
    date: str
    name: str
    merchant_name: Optional[str] = None
    pending: bool = False
    category: list[str] = Field(default_factory=list)
    payment_channel: Optional[str] = None
    raw: dict[str, Any]
    created_at: datetime
    updated_at: datetime
