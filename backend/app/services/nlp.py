# backend/app/services/nlp.py
from collections import defaultdict
import spacy

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("zh_core_web_sm")
    return _nlp

CATEGORY_MAP = {
    "PERSON": "人物",
    "PER": "人物",
    "ORG": "組織品牌",
    "LOC": "地點",
    "GPE": "地點",
    "DATE": "時間日期",
    "TIME": "時間日期",
    "PRODUCT": "產品",
    "CARDINAL": "數字",
    "MONEY": "金額",
}

def extract_entities(text: str) -> dict:
    if not text or not text.strip():
        return {"total": 0, "categories": {}}

    nlp = _get_nlp()
    doc = nlp(text[:10000])

    categories: dict[str, list[str]] = defaultdict(list)
    for ent in doc.ents:
        label = CATEGORY_MAP.get(ent.label_, "其他")
        categories[label].append(ent.text)

    total = sum(len(v) for v in categories.values())
    return {
        "total": total,
        "categories": {k: list(set(v)) for k, v in categories.items()},
    }

def group_entities_by_category(articles_entities: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, set] = defaultdict(set)
    for article in articles_entities:
        for category, entities in article.get("categories", {}).items():
            for entity in entities:
                grouped[category].add(entity)
    return {k: sorted(v) for k, v in grouped.items()}
