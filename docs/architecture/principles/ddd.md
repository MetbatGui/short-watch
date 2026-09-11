# DDD (Domain-Driven Design)

## 코어 원칙

### 도메인 경계

비즈니스 로직을 명확한 도메인으로 분리. 각 도메인은 독립적 책임을 가짐.

### 도메인 독립성

- 각 도메인은 독립적 저장소 유지
- 도메인 내부 구현은 외부에 노출하지 않음

### 느슨한 결합

- 도메인 간 참조는 ID만 사용
- 직접적 객체 참조 금지

### 응집도

도메인 간 관계는 Application Layer에서 조율. 도메인 자체는 순수 비즈니스 로직만 포함.

---

## 4계층 아키텍처 (Clean Architecture)

```
┌──────────────────────────────────────────────┐
│  Presentation          Infrastructure         │
│  (API router)          (DB/외부 API 구현)      │
│         │                      │              │
│         └──────────┬───────────┘              │
│                    ▼                          │
│         ┌──────────────────────┐              │
│         │   Application         │              │
│         │  (Use Case/Command)   │              │
│         │         │             │              │
│         │         ▼             │              │
│         │  ┌─────────────────┐  │              │
│         │  │     Domain      │  │              │
│         │  │  (Entity, VO,   │  │              │
│         │  │   Service)      │  │              │
│         │  └─────────────────┘  │              │
│         └──────────────────────┘              │
└──────────────────────────────────────────────┘
```

**의존성 규칙:** Domain ← Application ← (Presentation, Infrastructure)

**예외 — 수집기(Collector) Slice는 Domain 계층 생략 가능**: 원본 데이터를 판단 없이 그대로 저장하는 Bronze 수집기는 파싱/검증할 게 없어 Domain 모델이 불필요할 수 있다. 근거: [collector-bronze-no-transformation ADR](../../decisions/2026-09-12-collector-bronze-no-transformation.md).

- Domain: 외부 의존 없음 (표준 라이브러리만)
- Application: Domain만 import
- Presentation/Infrastructure: Domain, Application import 가능

---

## 디렉토리 구조 (예시)

```
modules/{context}/
├── domain/
│   ├── models.py              # Entity/Value Object (Aggregate Root 포함)
│   ├── events.py              # Domain Event
│   ├── services.py            # Domain Service (비즈니스 규칙)
│   └── repository.py          # Repository 인터페이스 (Port)
├── application/
│   ├── ports.py                # Port (Protocol)
│   ├── services.py             # Application Service / Use Case
├── infrastructure/
│   ├── {external}_client.py    # 외부 API 어댑터
│   └── repositories.py         # Repository 구현
├── presentation/ (또는 별도 api 계층)
│   └── router.py
└── __init__.py
```

---

## 지켜야 할 규칙 3가지

1. **Domain은 외부 import 금지**

   ```python
   # ❌ 금지
   from sqlalchemy import Column
   from fastapi import APIRouter

   # ✅ OK
   from typing import List
   ```
2. **Application은 Domain만 import**

   ```python
   # ❌ 금지
   from modules.news.infrastructure.persistence import SQLAlchemyNewsRepository

   # ✅ OK
   from modules.news.domain.repository import NewsRepository
   from modules.news.domain.models import News
   ```
3. **Presentation/Composition Root가 의존성 조립 담당**

   ```python
   # bootstrap.py 또는 presentation/router.py
   repo = SQLAlchemyNewsRepository(db_session)
   service = FetchNewsService(repo)
   ```

---

## CLI Presentation 규약

Presentation 계층은 HTTP API(router)뿐 아니라 **CLI(cron이 실행하는 명령어)도 포함**한다. HTTP의 status code+response body 자리를 CLI에선 다음으로 대신한다.

- **종료 코드(exit code)는 `0`(성공) / `1`(실패) 두 가지만 쓴다.** 그 이상 세분화하지 않는다 — Bash가 `2`를 "쉘 내장명령어 오용"으로 이미 예약해뒀기 때문에 임의로 재사용하면 관례와 충돌한다.
- **세부 사유는 UseCase 반환값을 그대로 구조화된 JSON으로 출력**해서 구분한다 (`typer.echo(json.dumps(result))`). 성공/실패 모두 `code` 필드(예: `OK_COLLECTED`, `OK_NO_DATA`, `ERR_LOGIN_FAILED`)를 포함한다. exit code는 "성공/실패 대분류"만, `code`는 "왜"를 담당한다 — HTTP의 `status_code`+`detail` 구조와 대응된다.
- **테스트는 Typer/Click의 `CliRunner`로 인메모리 실행**한다. `result.exit_code`로 대분류를, `json.loads(result.output)["code"]`로 세부 사유를 검증한다. FastAPI `TestClient`의 `response.status_code`+`response.json()`과 대응되는 방식이다.
