# backend/app/services/job_runner.py
import asyncio
from app.database import get_supabase
from app.services.serper import search_google
from app.services.scraper import fetch_articles_concurrent
from app.services.nlp import extract_entities, group_entities_by_category
from app.services.sheets import write_analysis_to_sheet

async def run_analysis_job(job_id: str, user_id: str, keyword: str, sheet_id: str, sheet_url: str, refresh_token: str | None = None):
    db = get_supabase()

    async def update_status(status: str, error: str | None = None):
        update_data = {"status": status}
        if error:
            update_data["error_msg"] = error
        await asyncio.to_thread(
            lambda: db.table("query_history").update(update_data).eq("job_id", job_id).execute()
        )

    try:
        await update_status("searching")
        serp_results = await search_google(keyword)

        await update_status("crawling")
        urls = [r["url"] for r in serp_results]
        texts = await fetch_articles_concurrent(urls)

        await update_status("analyzing")
        articles = []
        for result, text in zip(serp_results, texts):
            entities = extract_entities(text) if text else {"total": 0, "categories": {}}
            articles.append({**result, "entities": entities})

        grouped = group_entities_by_category([a["entities"] for a in articles])

        await update_status("writing")
        # run_in_executor prevents blocking the event loop during gspread I/O
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, write_analysis_to_sheet, sheet_id, keyword, articles, grouped, refresh_token)

        await asyncio.to_thread(
            lambda: db.table("query_history").update({
                "status": "done",
                "sheet_url": sheet_url,
            }).eq("job_id", job_id).execute()
        )

    except Exception as e:
        await update_status("failed", str(e)[:500])
