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
