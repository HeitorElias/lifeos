from fastapi import Request, HTTPException
from functools import wraps
import jwt
import os
from datetime import datetime, timezone

JWT_SECRET = os.environ.get('JWT_SECRET', 'lifeos_default_secret')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')


async def get_current_user(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('exp') and datetime.fromtimestamp(payload['exp'], tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token expirado")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
