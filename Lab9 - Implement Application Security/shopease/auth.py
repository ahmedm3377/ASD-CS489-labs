import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
import bcrypt
import hashlib
import base64

from .db import get_session
from .models import Customer

# Config
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/adsweb/api/v1/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        # pre-hash the provided password with SHA-256, then base64-encode
        pw_bytes = plain_password.encode("utf-8")
        pre = hashlib.sha256(pw_bytes).digest()
        encoded = base64.b64encode(pre)
        # hashed_password stored as utf-8 string
        return bcrypt.checkpw(encoded, hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    # pre-hash the password with SHA-256 and base64-encode the digest
    pw_bytes = password.encode("utf-8")
    pre = hashlib.sha256(pw_bytes).digest()
    encoded = base64.b64encode(pre)
    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt())
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(session, email: str):
    return session.query(Customer).filter(Customer.email == email).first()


def authenticate_user(session, email: str, password: str):
    user = get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def get_current_user(token: str = Depends(oauth2_scheme)) -> Customer:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except jwt.PyJWTError:
        raise credentials_exception

    session = get_session()
    try:
        user = get_user_by_email(session, token_data.email)
        if user is None:
            raise credentials_exception
        return user
    finally:
        session.close()


def require_role(required_roles: list[str]):
    def role_checker(current_user: Customer = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_checker


# Routes helpers for login/signup will be used from app.py
