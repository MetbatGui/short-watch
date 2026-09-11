# Testing 원칙

> TDD 순서(Red-Green-Refactor) 자체는 [xp.md § TDD](xp.md)에 있다. 이 문서는 "테스트를 어떻게 쓰나"만 다룬다.

---

## 1. Classicist 지향 (State Verification), Mockist 지양

Martin Fowler "Mocks Aren't Stubs"의 구분을 따른다.

- **Classical**: 되는 한 진짜 객체를 쓰고, 정말 애매할 때만 대역을 쓴다. **State Verification** — 결과(반환값, 저장된 상태, 부수효과의 최종 모습)로 검증한다.
- **Mockist**: 흥미로운 동작이 있는 협력객체는 다 mock으로 바꾼다. **Behavior Verification** — "무엇을 호출했나"로 검증한다.

이 프로젝트는 **Classical**을 지향한다.

### 적용 규칙

- **테스트는 결과로 검증한다.** "이 메서드가 호출됐나"가 아니라 "반환값/저장된 데이터가 뭔가"를 비교한다.
- **Test double은 진짜 쓰기 애매한 경계에서만 쓴다** — 외부 네트워크, 시간(sleep)처럼 실제로 못 쓰는 경우. 그 안에서는 `unittest.mock.MagicMock`(호출기록+행동검증 프레임워크)보다 **직접 작성한 Fake 클래스**(진짜로 동작하는 가벼운 구현)를 우선한다.
- **호출횟수 자체가 계약일 때도** (예: "3회 재시도한다") `Mock.call_count`가 아니라 **Fake가 스스로 기록한 로그를 상태로서 확인**한다 — Fake 자체의 상태를 들여다보는 것이지, 목킹 프레임워크의 기대치 검증 기능을 쓰는 게 아니다.

**판단 신호**: `assert_called_with`, `Mock().call_count`, `side_effect`를 쓰고 있다면 Mockist로 새고 있다는 뜻이다.

### Fake 작성 예시

```python
class FakeSession:
    """requests.Session 자리에 넣는 가벼운 진짜 구현. 큐에 넣은 응답을 순서대로 돌려주고,
    자신이 받은 요청을 calls에 기록한다 — 이 calls가 곧 검증 대상 '상태'다."""

    def __init__(self, responses: list):
        self._responses = iter(responses)
        self.calls: list[tuple[str, str]] = []  # (method, url)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url))
        response = next(self._responses)
        if isinstance(response, Exception):
            raise response
        return response

# 테스트에서
fake = FakeSession([login_ok, ConnectionError(), ConnectionError(), data_ok])
client = KrxFuturesClient(username="u", password="p", session=fake, sleep=lambda s: None)

result = client.fetch_raw(date(2026, 9, 11))

assert result == expected_rows           # State Verification: 결과값
assert len(fake.calls) == 4              # Fake 자신의 상태를 확인 (Mock.call_count 아님)
```

`tests/future/test_krx_futures_client.py`가 이 패턴(`FakeSession`/`FakeResponse`, `tests/future/fakes.py`)의 실제 적용 예시다.

---

## 2. 테스트 종류 & 마커

| 테스트 유형 | 역할 | 마커 |
|-----------|------|------|
| Unit (Fake) | 비즈니스 로직 → 빠른 검증 | `@pytest.mark.unit` |
| Integration | 계층 경계 계약 → Slice 완료 기준 | `@pytest.mark.integration` |
| Acceptance | Slice 단위 인수 기준 | `@pytest.mark.acceptance` |
| E2E | 외부 서비스 연동 → 배포 전/주기적 | `@pytest.mark.e2e` |

마커는 `pyproject.toml`의 `[tool.pytest.ini_options] markers`에 등록돼있다. `pytest -m unit`처럼 타입별 실행 가능.

## 3. 디렉토리 구조 = 도메인 기준, 타입은 마커로

```
tests/
  future/
    test_collect_acceptance.py   # @pytest.mark.acceptance
    test_krx_futures_client.py   # @pytest.mark.unit
```

`tests/unit/`, `tests/integration/`처럼 타입을 상위 폴더로 먼저 쪼개지 않는다. FastAPI 공식 템플릿(`tests/api/routes/`, `tests/crud/`) 등 비슷한 규모 레포도 기능 기준 폴더만 쓰고 타입은 파일명/마커로 구분한다 — 타입별 폴더는 도메인이 늘어날수록 같은 폴더명이 타입 수만큼 중복되고, "이 도메인 테스트 다 보기"가 여러 폴더에 흩어져서 불편해진다.

**주의**: 테스트 디렉토리에 `__init__.py`를 만들지 않는다 — 소스 패키지명과 겹치면 pytest가 잘못된 모듈을 import한다. 상세: [트러블슈팅](../../troubleshooting/2026-09-11-test-dir-name-collides-with-package.md).

## 4. Docstring = GWT (Given-When-Then)

모든 테스트(Unit, Integration, Acceptance, E2E) docstring은 GWT 형식.

```python
def test_get_news_returns_valid_response(client):
    """GET /news 는 유효한 응답을 반환한다.

    Given: FastAPI test client
    When: GET /news 호출
    Then: 200 OK + GetNewsResponse schema 유효
    """
    response = client.get("/news")
    assert response.status_code == 200
    GetNewsResponse.model_validate(response.json())
```

**규칙**:
- **Given은 명시적** — 암묵적 상태 가정 금지. 필요 시 fixture로 표현(`filled_repository`, `empty_repository` 등).
- Given이 서로 충돌하는 테스트 = 다른 fixture 필요.
- Docstring 첫 줄 = 사용자 관점 한 줄 요약.
