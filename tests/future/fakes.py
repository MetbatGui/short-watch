"""KrxFuturesClient 테스트용 Fake. requests.Session 자리에 넣는 가벼운 진짜 구현.

MagicMock(호출기록+행동검증)이 아니라 실제로 동작하는 대역을 쓴다 — Classicist 지향.
검증은 반환값(State)과 fake가 스스로 기록한 calls(Fake 자신의 State)로 한다.
(docs/architecture/principles/testing.md § 1)
"""


class FakeResponse:
    """requests.Response 자리 대역. json()이 성공하거나 지정한 예외를 던진다."""

    def __init__(self, data: dict | None = None, json_error: Exception | None = None):
        self._data = data
        self._json_error = json_error

    def json(self) -> dict:
        if self._json_error is not None:
            raise self._json_error
        return self._data


class FakeSession:
    """requests.Session 자리 대역.

    생성 시 넘긴 queue를 get()/post() 호출마다 하나씩 순서대로 소비한다.
    큐 항목이 Exception이면 그대로 raise(네트워크 오류 재현), 아니면 그대로 반환한다.
    받은 모든 요청을 calls에 기록한다 — 검증은 이 calls를 본다.
    """

    def __init__(self, queue: list):
        self._queue = iter(queue)
        self.calls: list[tuple[str, str]] = []
        self.cookies = _FakeCookies()

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(("GET", url))
        return self._next()

    def post(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(("POST", url))
        return self._next()

    def _next(self) -> FakeResponse:
        try:
            item = next(self._queue)
        except StopIteration:
            raise AssertionError(
                f"FakeSession 큐가 소진됨 (호출 {len(self.calls)}회: {self.calls}). "
                "테스트에 넘긴 큐 항목 개수를 확인해라."
            ) from None
        if isinstance(item, Exception):
            raise item
        return item


class _FakeCookies:
    def set(self, *args, **kwargs) -> None:
        pass
