"""Фильтрация ответов GigaChat: латиница и JSON-мусор не должны доезжать до UI."""
from __future__ import annotations

from app.services.naming_service import NamingService


def test_parse_variants_rejects_latin_titles() -> None:
    """Варианты с латиницей в title должны отсекаться до возврата пользователю."""
    raw = """
    {
      "variants": [
        {"title": "Короли и Сыновья", "style": "буквальный", "comment": "Прямой перевод."},
        {"title": "Наследие Короля", "style": "нейтрально-маркетинговый", "comment": "Подчёркивает преемственность."},
        {"title": "Коронованные Наследники", "style": "короткий и звучный", "comment": "Кратко и запоминающе."},
        {"title": "KING and SONS logo design", "style": "modern", "comment": "elegant typography"},
        {"title": "KING and SONS business card", "style": "clean", "comment": "subtle monogram"}
      ]
    }
    """
    variants = NamingService.parse_variants(raw)
    assert len(variants) == 3
    for v in variants:
        assert not any(c.isascii() and c.isalpha() for c in v["title"]), (
            f"Latin letters leaked into title: {v['title']!r}"
        )


def test_normalize_cleans_json_noise_from_comments() -> None:
    """В комментариях не должно оставаться фрагментов JSON-синтаксиса."""
    noisy = [
        {
            "title": "Наследие Короля",
            "style": "нейтрально-маркетинговый",
            "comment": "Подчёркивает преемственность и семейные традиции. }, {",
        },
        {
            "title": "Коронованные Наследники",
            "style": "короткий и звучный",
            "comment": "}, { Кратко и запоминающе звучит. }, {",
        },
    ]
    cleaned = NamingService._normalize_candidates(noisy)
    assert len(cleaned) == 2
    for v in cleaned:
        assert "}" not in v["comment"]
        assert "{" not in v["comment"]
        assert not v["comment"].endswith(",")
        assert not v["comment"].startswith(",")


def test_parse_variants_all_latin_returns_empty() -> None:
    """Если GigaChat ответил только по-английски — вернём пустой список.

    Это триггерит strict-ре-запрос в `generate()` выше по стеку.
    """
    raw = """
    {
      "variants": [
        {"title": "KING and SONS tower", "style": "modern", "comment": "elegant"},
        {"title": "KING and SONS plaza", "style": "bold", "comment": "confident"}
      ]
    }
    """
    variants = NamingService.parse_variants(raw)
    assert variants == []


def test_is_russian_title_rules() -> None:
    assert NamingService._is_russian_title("Башни Верха")
    assert NamingService._is_russian_title("Апсайд Тауэрс")
    assert not NamingService._is_russian_title("Upside Towers")
    assert not NamingService._is_russian_title("Башни Upside")
    assert not NamingService._is_russian_title("")
    assert not NamingService._is_russian_title("   ")
    assert not NamingService._is_russian_title("123 !!!")
