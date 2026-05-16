# backend/app/services/sheets.py
import base64
import json
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials as SACredentials
from app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

_gc = None

def _get_gc():
    global _gc
    if _gc is None:
        raw = base64.b64decode(settings.google_service_account_b64 or "e30=")
        creds_dict = json.loads(raw)
        creds = SACredentials.from_service_account_info(creds_dict, scopes=SCOPES)
        _gc = gspread.authorize(creds)
    return _gc


def _get_gc_oauth(refresh_token: str):
    creds = OAuthCredentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def create_user_sheet_oauth(refresh_token: str, user_email: str) -> tuple[str, str]:
    gc = _get_gc_oauth(refresh_token)
    spreadsheet = gc.create(f"SEO Entity 分析 - {user_email}")
    return spreadsheet.id, spreadsheet.url


def write_analysis_to_sheet(sheet_id: str, keyword: str, articles: list[dict], grouped: dict, refresh_token: str | None = None) -> None:
    gc = _get_gc_oauth(refresh_token) if refresh_token else _get_gc()
    spreadsheet = gc.open_by_key(sheet_id)

    # === 工作表1：文章分析（批次寫入）===
    try:
        ws1 = spreadsheet.worksheet("文章Entity分析")
        spreadsheet.del_worksheet(ws1)
    except gspread.WorksheetNotFound:
        pass
    ws1 = spreadsheet.add_worksheet(title="文章Entity分析", rows=max(20, len(articles) + 5), cols=15)

    rows1 = [["排名", "標題", "URL", "Entity總數", "人物", "組織品牌", "地點", "時間日期", "產品", "其他"]]
    for i, article in enumerate(articles, 1):
        cats = article["entities"].get("categories", {})
        rows1.append([
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
        ])
    ws1.update(rows1, "A1")

    # === 工作表2：Entity 分群（批次寫入）===
    try:
        ws2 = spreadsheet.worksheet("Entity分群")
        spreadsheet.del_worksheet(ws2)
    except gspread.WorksheetNotFound:
        pass
    total_entities = sum(len(entities) for entities in grouped.values())
    ws2 = spreadsheet.add_worksheet(title="Entity分群", rows=max(100, total_entities + 10), cols=3)

    rows2 = [["類別", "Entity", "出現篇數"]]
    for category, entities in grouped.items():
        for entity in entities:
            count = sum(
                1 for a in articles
                if entity in a["entities"].get("categories", {}).get(category, [])
            )
            rows2.append([category, entity, count])
    ws2.update(rows2, "A1")

    # === 工作表3：圖表說明（批次寫入）===
    try:
        ws3 = spreadsheet.worksheet("圖表")
        spreadsheet.del_worksheet(ws3)
    except gspread.WorksheetNotFound:
        pass
    ws3 = spreadsheet.add_worksheet(title="圖表", rows=5, cols=2)
    ws3.update([
        ["關鍵字", keyword],
        ["分析完成", "請至「文章Entity分析」工作表查看圖表資料"],
        ["提示", "選取A欄和D欄資料，插入->圖表->長條圖"],
    ], "A1")
