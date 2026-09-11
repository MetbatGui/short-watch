# AGENTS.md

> 이 파일은 템플릿이다. `{{ }}` 로 표시된 부분과 라우팅 표를 프로젝트에 맞게 채워라.

## 지식 저장 정책

**모든 학습/규칙/결정은 프로젝트 문서에 기록. 에이전트 로컬 메모리 사용 금지.**

- 새 규칙/피드백 → `AGENTS.md` 또는 `docs/` 해당 문서에 직접 반영
- 설계 결정 → ADR (`docs/decisions/`)
- Codex/Claude 공통 SSOT = 리포 내 마크다운
- **이 파일이 SSOT.** `CLAUDE.md` 는 이 파일을 가리키는 포인터일 뿐 — 내용 복사/이전 금지
- 에이전트 전용 설정(skill, hook, MCP)은 `.claude/` · `.codex/` 등 각자 위치에. 지침 파일에 중복 금지
- **Why:** SSOT 단일화, 에이전트 간 이식성, drift 방지, git 이력 추적

---

## 언어 정책

**모든 산출물 한국어 작성**:

- Docstring, 커밋 메시지, 문서, 대화, 코드 리뷰, 주석 모두 한국어
- 예외: 코드 식별자 (변수/함수/클래스명) 는 영어
- 사용자가 명시적으로 요청하지 않는 한 다른 언어 사용 금지

---

## 커밋 컨벤션

```
{GITMOJI}{type}: {title}

{description}          ← 필수
- {detail}             ← 선택 (복잡한 작업만)
```

gitmoji는 type에 붙여 쓴다: `✨feat` `🐛fix` `♻️refactor` `📝docs` `🧪test` `🔧chore`

상세 규칙·예시: [git-workflow.md § Commit 메시지](docs/git-workflow.md)

---

## 설계 결정 순서 (ADR 강제)

**설계 결정이 트리거 매칭 시 코드·문서 변경 전에 ADR 먼저**:

1. **Trigger 매칭 확인** ([adr-process.md](docs/adr-process.md) 표):
   - Domain 계약 (id/필드/invariant), 모듈 경계, 저장소 전략, 외부 dep, 원칙, 프로세스
2. **ADR 작성/갱신** (`docs/decisions/YYYY-MM-DD-{slug}.md`) + 인덱스 갱신
3. **Docs 갱신** (spec/plan/AGENTS/convention) — ADR 링크 명시
4. **변경 착수**

**예외 없음**. 유저가 "그냥 코드부터" 라 해도:
- "설계 trigger 매칭. ADR 먼저 작성. 승인?" **되물음**
- 승인 없이 trigger 관련 착수 금지

**판단 기준(과잉 적용 주의)**: 트리거 표에 형식적으로 걸린다고 전부 ADR 대상은 아니다. 실질 질문은 "미래 세션이 '왜 이 선택?' 물었을 때 답이 필요한가" — 대안 간 실질적 tradeoff 가 있고, 근거를 안 적으면 나중에 누군가 조용히 되돌릴 위험이 있는 결정만 ADR 대상이다. 한 줄짜리 관례 추가, trivial 하고 되돌리기 쉬운 선택까지 ADR 로 만들면 오히려 문서 부담만 커진다.

ADR 형식·Superseded 처리·immutable 원칙은 [adr-process.md](docs/adr-process.md).

---

## 코드 작성 순서 (TDD 강제)

**모든 프로덕션 코드는 실패하는 test 부터.**
Red-Green-Refactor 실행 방식은 [xp.md § TDD](docs/architecture/principles/xp.md).

**예외 없음**. 유저가 "일단 X 만들어봐" / "먼저 model 부터" 라 해도:
- "TDD 순서상 test 부터 작성하겠음. 승인?" **되물음**
- 승인 없이 프로덕션 파일 생성/편집 금지

**위반 판정**: 같은 slice 에 관련 test 없이 프로덕션 파일 만듦.

---

## 언제 무엇을 볼까

> 프로젝트별 문서가 늘어날수록 이 표를 채워라. 표가 비어 있으면 "어디 봐야 하지" 를 매번 다시 찾아야 한다 — 그 자체가 SSOT 붕괴의 시작이다.

| 상황 | 문서 |
|------|------|
| 이 기능이 제품 방향에 맞나 / 우선순위 판단 | [product-vision.md](docs/product-vision.md) |
| 커밋 메시지 형식 (상세 규칙·예시) | [git-workflow.md § Commit 메시지](docs/git-workflow.md) |
| 커밋 단위 (원자성, 언제 커밋할지) | [git-workflow.md § 원자적 커밋](docs/git-workflow.md) |
| 순수 docs 변경은 어떻게 (직접 master?) | [git-workflow.md § 문서 전용 변경](docs/git-workflow.md) |
| 브랜치 만들 때 / PR 만들 때 (단위·이름·master green 규칙) | [git-workflow.md § 브랜치 전략](docs/git-workflow.md) |
| PR 크기 (언제 분리?) | [git-workflow.md § PR 크기 원칙](docs/git-workflow.md) |
| PR 리뷰 (severity, nit 상한, 저자 응답 형식) | [review-standard.md](docs/review-standard.md) |
| 개발 플로우 (Spike → Spec → Plan → Tasks → Skeleton → 구현) | [workflow.md](docs/workflow.md) |
| 새 slice 시작 (Spec/Plan/Task 순서) | [vertical-slices.md](docs/architecture/principles/vertical-slices.md) |
| TDD 순서 헷갈림 (Red-Green-Refactor) | [xp.md](docs/architecture/principles/xp.md) |
| 테스트 어떻게 쓰나 (GWT, 마커, 디렉토리, Classicist/Fake) | [testing.md](docs/architecture/principles/testing.md) |
| 도메인 계층 애매 (4계층 어디에?) | [ddd.md](docs/architecture/principles/ddd.md) |
| ADR (아키텍처 결정 이력) | [docs/decisions/](docs/decisions/) — index: [README](docs/decisions/README.md) |
| ADR 프로세스 (언제/어떻게 쓰나) | [adr-process.md](docs/adr-process.md) |
| Spike/조사 결과 참조 | `docs/research/` |
| 트러블슈팅 기록 (버그/장애 원인·해결 과정) | [docs/troubleshooting/](docs/troubleshooting/) — index: [README](docs/troubleshooting/README.md) |
| Slice Spec (무엇을 만들 것인가) | [docs/specs/](docs/specs/) — index: [README](docs/specs/README.md) |
| Slice Plan (어떻게 만들 것인가, Task 순서) | [docs/plans/](docs/plans/) — index: [README](docs/plans/README.md) |
| {{프로젝트별 항목 추가}} | {{경로}} |

---

## 프로젝트 실행 명령

> 스택에 맞게 채워라. 예: `uv run pytest`, `npm test`, `just check-branch-green` 등.

```bash
uv run pytest
uv run main.py
```

초기 설정은 [README § 빠른 시작](README.md) 참고.
