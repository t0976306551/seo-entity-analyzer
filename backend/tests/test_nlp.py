# backend/tests/test_nlp.py
import pytest
from app.services.nlp import extract_entities, group_entities_by_category

def test_extract_entities_returns_dict():
    text = "蘋果公司在台灣推出iPhone 16，執行長Tim Cook親自出席。"
    result = extract_entities(text)
    assert isinstance(result, dict)
    assert "total" in result
    assert "categories" in result
    assert result["total"] >= 0

def test_extract_entities_counts_correctly():
    text = "台灣大哥大和中華電信都有提供4G吃到飽方案。"
    result = extract_entities(text)
    assert result["total"] >= 0
    assert isinstance(result["categories"], dict)

def test_group_entities_by_category():
    articles_entities = [
        {"total": 3, "categories": {"組織品牌": ["台灣大哥大"], "地點": ["台灣", "台北"]}},
        {"total": 2, "categories": {"組織品牌": ["中華電信", "遠傳"]}},
    ]
    result = group_entities_by_category(articles_entities)
    assert "組織品牌" in result
    assert "台灣大哥大" in result["組織品牌"]
    assert "中華電信" in result["組織品牌"]

def test_empty_text_returns_zero():
    result = extract_entities("")
    assert result["total"] == 0
    assert result["categories"] == {}


def test_extract_entities_with_empty_string():
    """空字串輸入應正常回傳 zero，不拋出例外"""
    from app.services.nlp import extract_entities
    result = extract_entities("")
    assert result["total"] == 0
    assert result["categories"] == {}

def test_extract_entities_very_long_text():
    """Text longer than 10000 chars should be truncated and still work"""
    from app.services.nlp import extract_entities
    long_text = "台灣大哥大 " * 2000  # ~12000 chars
    result = extract_entities(long_text)
    assert isinstance(result, dict)
    assert result["total"] >= 0

def test_group_entities_empty_list():
    """Empty article list should return empty dict"""
    from app.services.nlp import group_entities_by_category
    result = group_entities_by_category([])
    assert result == {}

def test_group_entities_deduplication():
    """Same entity in multiple articles should appear once in grouped result"""
    from app.services.nlp import group_entities_by_category
    articles = [
        {"total": 1, "categories": {"組織品牌": ["台灣大哥大"]}},
        {"total": 1, "categories": {"組織品牌": ["台灣大哥大"]}},
        {"total": 1, "categories": {"組織品牌": ["台灣大哥大"]}},
    ]
    result = group_entities_by_category(articles)
    assert result["組織品牌"].count("台灣大哥大") == 1  # deduplicated


def test_extract_entities_total_matches_categories():
    """BUG-1 修復驗證：total 應等於去重後各 category 長度的總和"""
    from app.services.nlp import extract_entities
    # 這段文字故意讓「台灣大哥大」出現多次，以觸發去重前後不一致的問題
    text = "台灣大哥大提供4G方案，台灣大哥大的月租費是599元，台灣大哥大很受歡迎。"
    result = extract_entities(text)
    deduped_total = sum(len(v) for v in result["categories"].values())
    assert result["total"] == deduped_total, (
        f"total ({result['total']}) should equal sum of deduped category lengths ({deduped_total})"
    )


def test_extract_entities_whitespace_only():
    """純空白字串應回傳 zero"""
    from app.services.nlp import extract_entities
    result = extract_entities("   ")
    assert result["total"] == 0
    assert result["categories"] == {}
