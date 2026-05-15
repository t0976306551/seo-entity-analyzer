# backend/app/services/sheets.py
import base64
import json
import gspread
from google.oauth2.service_account import Credentials
from app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _get_gc():
    raw = base64.b64decode(settings.google_service_account_b64 or "e30=")
    creds_dict = json.loads(raw)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def create_user_sheet(user_email: str) -> tuple[str, str]:
    """建立專屬 Sheet，回傳 (sheet_id, sheet_url)"""
    gc = _get_gc()
    spreadsheet = gc.create(f"SEO Entity 分析 - {user_email}")
    spreadsheet.share(user_email, perm_type="user", role="writer", notify=False)
    return spreadsheet.id, spreadsheet.url

def write_analysis_to_sheet(sheet_id: str, keyword: str, articles: list[dict], grouped: dict) -> None:
    """
    articles: list of {url, title, snippet, entities: {total, categories}}
    grouped: dict of {category: [entity, ...]}
    """
    gc = _get_gc()
    spreadsheet = gc.open_by_key(sheet_id)

    # === 工作表1：文章分析 ===
    try:
        ws1 = spreadsheet.worksheet("文章Entity分析")
        spreadsheet.del_worksheet(ws1)
    except gspread.WorksheetNotFound:
        pass
    ws1 = spreadsheet.add_worksheet(title="文章Entity分析", rows=20, cols=15)

    headers = ["排名", "標題", "URL", "Entity總數", "人物", "組織品牌", "地點", "時間日期", "產品", "其他"]
    ws1.append_row(headers)

    for i, article in enumerate(articles, 1):
        cats = article["entities"].get("categories", {})
        row = [
            i,
            article.get("title", ""),
            article.get("url", ""),
            article["entities"].get("total", 0),
            len(cats.get("人物", [])),
            len(cats.get("組織品牌", [])),
            len(cats.get("地點", [])),
            len(cats.get("時間日期", [])),
            len(cats.get("產品", [])),
            len(cats.get("其他", [])),
        ]
        ws1.append_row(row)

    # === 工作表2：Entity 分群 ===
    try:
        ws2 = spreadsheet.worksheet("Entity分群")
        spreadsheet.del_worksheet(ws2)
    except gspread.WorksheetNotFound:
        pass
    ws2 = spreadsheet.add_worksheet(title="Entity分群", rows=100, cols=3)
    ws2.append_row(["類別", "Entity", "出現篇數"])

    for category, entities in grouped.items():
        for entity in entities:
            count = sum(
                1 for a in articles
                if entity in a["entities"].get("categories", {}).get(category, [])
            )
            ws2.append_row([category, entity, count])

    # === 工作表3：圖表說明 ===
    try:
        ws3 = spreadsheet.worksheet("圖表")
        spreadsheet.del_worksheet(ws3)
    except gspread.WorksheetNotFound:
        pass
    ws3 = spreadsheet.add_worksheet(title="圖表", rows=5, cols=2)
    ws3.append_row(["關鍵字", keyword])
    ws3.append_row(["分析完成", "請至「文章Entity分析」工作表查看圖表資料"])
    ws3.append_row(["提示", "選取A欄和D欄資料，插入->圖表->長條圖"])
