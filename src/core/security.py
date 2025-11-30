from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from src.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.FRONTEND_URL}/login")

class TokenData(BaseModel):
    user_id: str
    email: str
    roles: list[str] = []

def get_public_key():
    try:
        with open(settings.PUBLIC_KEY_PATH, "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        raise RuntimeError(f"Public key not found at {settings.PUBLIC_KEY_PATH}")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        public_key = get_public_key()
        payload = jwt.decode(token, public_key, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        roles: list[str] = payload.get("roles", [])
        
        if user_id is None or email is None:
            raise credentials_exception
            
        return TokenData(user_id=user_id, email=email, roles=roles)
    except jwt.PyJWTError:
        raise credentials_exception
