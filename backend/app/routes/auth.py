from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.db.mongo import get_db
from app.code.security import hash_password, verify_password, create_access_token
from app.models.user import UserCreate, Token, UserPublic
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic)
async def register(payload: UserCreate, db = Depends(get_db)):
    if await db.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    doc = payload.model_dump()
    doc["password_hash"] = hash_password(payload.password)
    del doc["password"]
    res = await db.users.insert_one(doc)
    saved = await db.users.find_one({"_id": res.inserted_id})
    if saved:
        saved["_id"] = str(saved["_id"])
    return saved

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token(subject=user["email"])
    logging.info(f"role {user["role"]}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"]
    }

@router.get("/ping")
async def ping():
    return {"msg": "NEW VERSION 123 🚀"}
