from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx


class PlaidAPIError(RuntimeError):
    pass


class PlaidService:
    def __init__(self) -> None:
        self.client_id = os.environ.get("PLAID_CLIENT_ID", "")
        self.secret = os.environ.get("PLAID_SECRET", "")
        plaid_env = os.environ.get("PLAID_ENV", "sandbox").lower()
        hosts = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }
        self.base_url = hosts.get(plaid_env, hosts["sandbox"])
        self.products = [p.strip() for p in os.environ.get("PLAID_PRODUCTS", "transactions").split(",") if p.strip()]
        self.country_codes = [c.strip() for c in os.environ.get("PLAID_COUNTRY_CODES", "US").split(",") if c.strip()]

    def configured(self) -> bool:
        return bool(self.client_id and self.secret)

    def _auth_payload(self) -> dict[str, str]:
        return {"client_id": self.client_id, "secret": self.secret}

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(f"{self.base_url}{path}", json={**self._auth_payload(), **payload})

        if response.status_code >= 400:
            raise PlaidAPIError(response.text)
        return response.json()

    async def create_link_token(self, user_id: str, client_name: str, language: str = "pt") -> dict[str, Any]:
        payload = {
            "user": {"client_user_id": user_id},
            "client_name": client_name,
            "products": self.products,
            "country_codes": self.country_codes,
            "language": language,
        }
        return await self._post("/link/token/create", payload)

    async def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        return await self._post("/item/public_token/exchange", {"public_token": public_token})

    async def sync_transactions(self, access_token: str, cursor: str | None = None) -> dict[str, Any]:
        added: list[dict[str, Any]] = []
        modified: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        has_more = True
        current_cursor = cursor

        while has_more:
            payload = {"access_token": access_token}
            if current_cursor:
                payload["cursor"] = current_cursor

            response = await self._post("/transactions/sync", payload)
            added.extend(response.get("added", []))
            modified.extend(response.get("modified", []))
            removed.extend(response.get("removed", []))
            has_more = response.get("has_more", False)
            current_cursor = response.get("next_cursor", current_cursor)

        return {
            "added": added,
            "modified": modified,
            "removed": removed,
            "next_cursor": current_cursor,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }


plaid_service = PlaidService()
