# backend/app/routers/auth.py
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from app.config import settings
from app.database import get_supabase
from app.auth import get_current_user
from app.services.sheets import create_user_sheet_oauth

router = APIRouter()

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

REDIRECT_URI = f"{settings.backend_url}/auth/google/callback"

_pending_oauth: dict[str, str] = {}  # user_id -> code_verifier


def _build_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=REDIRECT_URI,
    )


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=201)
async def register(request: AuthRequest, background_tasks: BackgroundTasks):
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

    try:
        db.table("user_sheets").insert({
            "user_id": user_id,
            "sheet_id": "",
            "sheet_url": "",
            "status": "pending",
        }).execute()
    except Exception:
        raise HTTPException(status_code=409, detail="User already exists")

    return {
        "user_id": user_id,
        "email": request.email,
        "message": "Registration successful. Please connect your Google account.",
    }


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
        "sheet_status": sheet_record.data.get("status", "pending") if sheet_record.data else "pending",
    }


@router.get("/google/url")
async def google_oauth_url(current_user: dict = Depends(get_current_user)):
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=current_user["user_id"],
    )
    verifier = getattr(flow, 'code_verifier', None)
    if verifier:
        _pending_oauth[current_user["user_id"]] = verifier
    return {"url": auth_url}


@router.get("/google/callback")
async def google_oauth_callback(code: str, state: str):
    user_id = state
    db = get_supabase()

    try:
        flow = _build_flow()
        code_verifier = _pending_oauth.pop(user_id, None)
        if code_verifier:
            flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
        creds = flow.credentials

        refresh_token = creds.refresh_token
        user_record = db.table("user_sheets").select("*").eq("user_id", user_id).maybe_single().execute()
        user_email = ""
        if user_record.data:
            auth_user = db.auth.admin.get_user_by_id(user_id)
            user_email = auth_user.user.email if auth_user.user else ""

        sheet_id, sheet_url = await asyncio.to_thread(
            create_user_sheet_oauth, refresh_token, user_email
        )

        db.table("user_sheets").update({
            "sheet_id": sheet_id,
            "sheet_url": sheet_url,
            "status": "active",
            "google_refresh_token": refresh_token,
        }).eq("user_id", user_id).execute()

    except Exception as e:
        import traceback
        print("=== GOOGLE CALLBACK ERROR ===")
        print(traceback.format_exc())
        print("============================")
        db.table("user_sheets").update({"status": "failed"}).eq("user_id", user_id).execute()
        return RedirectResponse(url=f"{settings.frontend_url}/dashboard?google_error=1&msg={str(e)[:100]}")

    return RedirectResponse(url=f"{settings.frontend_url}/dashboard?google_connected=1")
