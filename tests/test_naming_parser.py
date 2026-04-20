from app.services.naming_service import NamingService


def test_parse_variants_returns_unique_five() -> None:
    raw = """
    {
      "variants": [
        {"title": "Башни Верха", "style": "буквальный", "comment": "Близко к исходнику"},
        {"title": "Башни Верха", "style": "дубль", "comment": "дубликат"},
        {"title": "Вершинные Башни", "style": "маркетинговый", "comment": "Уверенно звучит"},
        {"title": "Вышебашенные", "style": "креативный", "comment": "Необычно"},
        {"title": "Апсайд Тауэрс", "style": "транслит", "comment": "Сохранение узнаваемости"},
        {"title": "Тауэры Пика", "style": "смелый", "comment": "Слогановый вариант"}
      ]
    }
    """
    variants = NamingService.parse_variants(raw)
    assert len(variants) == 5
    assert variants[0]["title"] == "Башни Верха"
    assert len({v["title"] for v in variants}) == 5


def test_parse_variants_invalid_shape() -> None:
    raw = '{"variants":"bad"}'
    try:
        NamingService.parse_variants(raw)
    except ValueError:
        assert True
        return
    assert False, "Expected ValueError"
