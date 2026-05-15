# backend/app/routers/history.py
from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.database import get_supabase

router = APIRouter()

@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    result = db.table("query_history") \
        .select("id, keyword, status, sheet_url, created_at, error_msg") \
        .eq("user_id", current_user["user_id"]) \
        .order("created_at", desc=True) \
        .limit(50) \
        .execute()
    return result.data or []
