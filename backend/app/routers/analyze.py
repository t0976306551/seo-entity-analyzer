# backend/app/routers/analyze.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.auth import get_current_user
from app.database import get_supabase
from app.services.job_runner import run_analysis_job

router = APIRouter()

class AnalyzeRequest(BaseModel):
    keyword: str

@router.post("/analyze", status_code=202)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    keyword = request.keyword.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    db = get_supabase()

    sheet_record = db.table("user_sheets").select("sheet_id, status").eq("user_id", user_id).single().execute()
    if not sheet_record.data or sheet_record.data.get("status") != "active":
        raise HTTPException(status_code=400, detail="User sheet not ready. Please re-register.")

    sheet_id = sheet_record.data["sheet_id"]
    job_id = str(uuid.uuid4())

    db.table("query_history").insert({
        "user_id": user_id,
        "keyword": keyword,
        "status": "pending",
        "job_id": job_id,
    }).execute()

    background_tasks.add_task(run_analysis_job, job_id, user_id, keyword, sheet_id)

    return {"job_id": job_id, "status": "pending"}

@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_supabase()
    result = db.table("query_history").select("*").eq("job_id", job_id).eq("user_id", current_user["user_id"]).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")

    return result.data
