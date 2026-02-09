from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/auth", tags=["Auth"])

mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'lifeos_default_secret')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _create_token(user_id: str, email: str, name: str, plan_id: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "plan_id": plan_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/register")
async def register(req: RegisterRequest):
    existing = await _db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "name": req.name,
        "email": req.email,
        "password_hash": _hash_password(req.password),
        "plan_id": "free",
        "role": "user",
        "onboarding_complete": False,
        "profile": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await _db.users.insert_one(user)
    
    token = _create_token(user_id, req.email, req.name, "free")
    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": req.name,
            "email": req.email,
            "plan_id": "free",
            "onboarding_complete": False
        }
    }


@router.post("/login")
async def login(req: LoginRequest):
    user = await _db.users.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    if not _verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = _create_token(user["id"], user["email"], user["name"], user.get("plan_id", "free"))
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "plan_id": user.get("plan_id", "free"),
            "onboarding_complete": user.get("onboarding_complete", False),
            "profile": user.get("profile", {})
        }
    }


@router.get("/me")
async def get_me(request: Request):
    from middleware.auth import get_current_user
    current = await get_current_user(request)
    user = await _db.users.find_one({"id": current["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user
