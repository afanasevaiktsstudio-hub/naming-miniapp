from app.storage.sqlite_store import SQLiteStore, UserSession


def test_sqlite_store_persists_session(tmp_path) -> None:
    db_path = tmp_path / "bot.db"
    store = SQLiteStore(str(db_path))
    store.set_session(
        123,
        UserSession(
            source_name="Neva Towers",
            variants=[{"title": "Нева Тауэрс", "style": "translit", "comment": "ok"}],
            selected_title="Нева Тауэрс",
        ),
    )
    loaded = store.get_session(123)
    assert loaded is not None
    assert loaded.source_name == "Neva Towers"
    assert loaded.selected_title == "Нева Тауэрс"


def test_sqlite_store_rate_limit(tmp_path) -> None:
    db_path = tmp_path / "rate.db"
    store = SQLiteStore(str(db_path))
    assert store.try_consume(1, "text", 2) is True
    assert store.try_consume(1, "text", 2) is True
    assert store.try_consume(1, "text", 2) is False
