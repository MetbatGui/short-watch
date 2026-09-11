from datetime import date
from typing import Protocol


class FuturesSourcePort(Protocol):
    def fetch_raw(self, target_date: date) -> list[dict]: ...


class FutureRawRepositoryPort(Protocol):
    def save_raw(self, target_date: date, rows: list[dict]) -> None: ...
