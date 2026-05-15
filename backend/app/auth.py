# backend/app/auth.py
from fastapi import Header, HTTPException
from app.database import get_supabase

async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or not parts[1]:
        raise HTTPException(status_code=401, detail="Missing token")
    token = parts[1]

    try:
        db = get_supabase()
        response = db.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": response.user.id, "email": response.user.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
