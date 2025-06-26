from fastapi import APIRouter, HTTPException
from .schemas import UserCreate, Token
import logging

router = APIRouter(prefix="", tags=["auth"])

# Логування дій користувача
logging.basicConfig(filename="audit.log", level=logging.INFO)

def log_action(user: str, action: str):
    logging.info(f"User: {user} | Action: {action}")

@router.post("/register")
def register(user: UserCreate):
    log_action(user.username, "Registered new account")
    return {
        "status": "success",
        "message": f"User '{user.username}' successfully registered",
        "user_id": 1,
        "username": user.username,
        "next_steps": "You can now login using your credentials at /login endpoint"
    }

@router.post("/login", response_model=Token)
def login(user: UserCreate):
    if user.username != "testuser" or user.password != "TestPass123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    log_action(user.username, "Successful login")
    return {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token"
    }

@router.post("/refresh", response_model=Token)
def refresh(token: dict):
    if not token.get("token"):
        raise HTTPException(status_code=400, detail="Token is required")
    log_action("testuser", "Refreshed token")
    return {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token"
    }
