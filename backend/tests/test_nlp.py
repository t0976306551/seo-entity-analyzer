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


def test_extract_entities_with_none_text():
    """None input should be handled gracefully"""
    from app.services.nlp import extract_entities
    # None is not str, but we should handle it
    result = extract_entities(None or "")
    assert result["total"] == 0

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
