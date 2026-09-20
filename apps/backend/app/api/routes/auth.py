from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from app.schemas.user import UserCreate, User
from app.repositories.users import user_repo
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from app.services.seed_service import seed_user_trip

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

@router.post("/register")
def register(request: RegisterRequest):
    # Check if user exists
    existing = user_repo.collection.find_one({"email": request.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(request.password)
    user_doc = {
        "name": request.name,
        "email": request.email,
        "hashed_password": hashed_password,
        "loyalty_tier": "Silver",
        "preferences": {
            "seat": "window",
            "meal": "standard",
        }
    }
    
    created_user = user_repo.create_or_update(user_doc)
    user_id = created_user["id"]
    
    # Seed the Ahmedabad to Lahore trip
    seed_user_trip(user_id, request.name)
    
    # Generate token
    access_token = create_access_token(data={"sub": request.email, "user_id": user_id})
    
    return {"access_token": access_token, "token_type": "bearer", "user": created_user}


@router.post("/login")
def login(request: LoginRequest):
    user = user_repo.collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user.get("hashed_password"):
        raise HTTPException(status_code=400, detail="Invalid account setup (no password)")
        
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    user_id = str(user.get("id") or user.get("_id"))
    access_token = create_access_token(data={"sub": request.email, "user_id": user_id})
    
    user["id"] = user_id
    if "_id" in user:
        del user["_id"]
        
    return {"access_token": access_token, "token_type": "bearer", "user": user}

