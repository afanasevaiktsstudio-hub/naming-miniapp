import json
import sqlite3
from dataclasses import dataclass
from datetime import date


@dataclass
class UserSession:
    source_name: str
    variants: list[dict[str, str]]
    selected_title: str | None = None


class SQLiteStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    variants_json TEXT NOT NULL,
                    selected_title TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER NOT NULL,
                    bucket TEXT NOT NULL,
                    day TEXT NOT NULL,
                    used INTEGER NOT NULL,
                    PRIMARY KEY (user_id, bucket, day)
                )
                """
            )
            conn.commit()

    def set_session(self, user_id: int, session: UserSession) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (user_id, source_name, variants_json, selected_title)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    source_name=excluded.source_name,
                    variants_json=excluded.variants_json,
                    selected_title=excluded.selected_title
                """,
                (
                    user_id,
                    session.source_name,
                    json.dumps(session.variants, ensure_ascii=False),
                    session.selected_title,
                ),
            )
            conn.commit()

    def get_session(self, user_id: int) -> UserSession | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT source_name, variants_json, selected_title FROM sessions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return UserSession(
            source_name=str(row["source_name"]),
            variants=json.loads(str(row["variants_json"])),
            selected_title=row["selected_title"],
        )

    def set_selected_title(self, user_id: int, selected_title: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET selected_title = ? WHERE user_id = ?",
                (selected_title, user_id),
            )
            conn.commit()

    def try_consume(self, user_id: int, bucket: str, limit: int) -> bool:
        today = date.today().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT used FROM rate_limits
                WHERE user_id = ? AND bucket = ? AND day = ?
                """,
                (user_id, bucket, today),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO rate_limits (user_id, bucket, day, used)
                    VALUES (?, ?, ?, 1)
                    """,
                    (user_id, bucket, today),
                )
                conn.commit()
                return True

            used = int(row["used"])
            if used >= limit:
                return False

            conn.execute(
                """
                UPDATE rate_limits SET used = ?
                WHERE user_id = ? AND bucket = ? AND day = ?
                """,
                (used + 1, user_id, bucket, today),
            )
            conn.commit()
            return True
