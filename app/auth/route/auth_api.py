import base64
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str
    stay_signed_in: Optional[bool] = False


@router.post("/login")
def login(payload: LoginRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="email and password are required")

    demo_email = os.environ.get("DEMO_ADMIN_EMAIL", "Admin123@ey.com")
    demo_password = os.environ.get("DEMO_ADMIN_PASSWORD", "Admin123@ey.com")
    if payload.email != demo_email or payload.password != demo_password:
        raise HTTPException(status_code=401, detail="invalid credentials")

    raw_token = f"{payload.email}:{os.urandom(24).hex()}"
    access_token = base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("ascii")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": True,
        "email": payload.email,
        "expires_in": 60 * 60 * (24 * 14 if payload.stay_signed_in else 8),
    }
