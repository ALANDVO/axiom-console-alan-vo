from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    sub: str
    roles: list[str] = []
    exp: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str = payload.get("sub")
        roles: list[str] = payload.get("roles", [])
        exp: int = payload.get("exp", 0)
        if sub is None:
            return None
        return TokenData(sub=sub, roles=roles, exp=exp)
    except JWTError:
        return None