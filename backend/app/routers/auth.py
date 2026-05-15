# backend/app/routers/auth.py
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_supabase
from app.services.sheets import create_user_sheet

router = APIRouter()

class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=201)
async def register(request: AuthRequest):
    db = get_supabase()

    try:
        auth_response = db.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not auth_response.user:
        raise HTTPException(status_code=400, detail="Registration failed")

    user_id = auth_response.user.id

    db.table("user_sheets").insert({
        "user_id": user_id,
        "sheet_id": "",
        "sheet_url": "",
        "status": "pending",
    }).execute()

    asyncio.create_task(_provision_sheet(user_id, request.email))

    return {
        "user_id": user_id,
        "email": request.email,
        "message": "Registration successful. Your Google Sheet is being prepared.",
    }

async def _provision_sheet(user_id: str, email: str):
    db = get_supabase()
    try:
        sheet_id, sheet_url = create_user_sheet(email)
        db.table("user_sheets").update({
            "sheet_id": sheet_id,
            "sheet_url": sheet_url,
            "status": "active",
        }).eq("user_id", user_id).execute()
    except Exception:
        db.table("user_sheets").update({"status": "failed"}).eq("user_id", user_id).execute()

@router.post("/login")
async def login(request: AuthRequest):
    db = get_supabase()

    try:
        auth_response = db.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not auth_response.session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    sheet_record = db.table("user_sheets").select("sheet_url, status").eq("user_id", auth_response.user.id).maybe_single().execute()

    return {
        "access_token": auth_response.session.access_token,
        "user_id": auth_response.user.id,
        "email": auth_response.user.email,
        "sheet_url": sheet_record.data.get("sheet_url", "") if sheet_record.data else "",
    }
