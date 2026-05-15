# backend/app/services/job_runner.py
import asyncio
from app.database import get_supabase
from app.services.serper import search_google
from app.services.scraper import fetch_articles_concurrent
from app.services.nlp import extract_entities, group_entities_by_category
from app.services.sheets import write_analysis_to_sheet

async def run_analysis_job(job_id: str, user_id: str, keyword: str, sheet_id: str):
    db = get_supabase()

    def update_status(status: str, error: str | None = None):
        update_data = {"status": status}
        if error:
            update_data["error_msg"] = error
        db.table("query_history").update(update_data).eq("job_id", job_id).execute()

    try:
        update_status("searching")
        serp_results = await search_google(keyword)

        update_status("crawling")
        urls = [r["url"] for r in serp_results]
        texts = await fetch_articles_concurrent(urls)

        update_status("analyzing")
        articles = []
        for result, text in zip(serp_results, texts):
            entities = extract_entities(text) if text else {"total": 0, "categories": {}}
            articles.append({**result, "entities": entities})

        grouped = group_entities_by_category([a["entities"] for a in articles])

        update_status("writing")
        write_analysis_to_sheet(sheet_id, keyword, articles, grouped)

        sheet_record = db.table("user_sheets").select("sheet_url").eq("user_id", user_id).single().execute()
        sheet_url = sheet_record.data.get("sheet_url", "") if sheet_record.data else ""

        db.table("query_history").update({
            "status": "done",
            "sheet_url": sheet_url,
        }).eq("job_id", job_id).execute()

    except Exception as e:
        update_status("failed", str(e)[:500])
        raise
