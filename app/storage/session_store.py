from dataclasses import dataclass


@dataclass
class UserSession:
    source_name: str
    variants: list[dict[str, str]]
    selected_title: str | None = None


class InMemorySessionStore:
    def __init__(self) -> None:
        self._data: dict[int, UserSession] = {}

    def set_session(self, user_id: int, session: UserSession) -> None:
        self._data[user_id] = session

    def get_session(self, user_id: int) -> UserSession | None:
        return self._data.get(user_id)
