from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Literal["student", "staff", "admin", "collector"] = "student"

class UserPublic(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    role: str

class UserInDB(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    password_hash: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"