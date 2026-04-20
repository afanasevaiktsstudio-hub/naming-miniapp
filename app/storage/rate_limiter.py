from datetime import date


class DailyRateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._counters: dict[int, tuple[date, int]] = {}

    def try_consume(self, user_id: int) -> bool:
        today = date.today()
        current = self._counters.get(user_id)
        if current is None or current[0] != today:
            self._counters[user_id] = (today, 1)
            return True

        _, used = current
        if used >= self.limit:
            return False
        self._counters[user_id] = (today, used + 1)
        return True
