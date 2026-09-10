# Plan Index

> Slice의 "어떻게 만들 것인가"를 정의한다 — 접합부 설계(Port/Domain/Endpoint 시그니처)와 Task 순서.
> Spec(무엇을)과는 분리한다 — [../specs/](../specs/).
> 파일 위치: `docs/plans/{slice}.md`. Milestone 폴더로 나누지 않는다.

---

## 작성 시점

workflow.md 5단계(Plan). Spec 확정 후에 쓴다.

## 형식

```markdown
# {slice} Plan

## Phase 1: Walking Skeleton
Stub + Integration test, 모든 계층

## Phase 2: 실제 구현
Inside-Out TDD, Stub 하나씩 교체

## Phase 3: 부가 기능

## Tasks
- [ ] task 1 (PR 1개)
- [ ] task 2 (PR 1개)
```

## GitHub Issue 미러

저장소(이 폴더의 markdown)가 SSOT. Slice Issue 본문에는 요약 + 이 파일 링크만 둔다. 전문 복사 안 함.

---

## 목록

| Slice | Plan |
|-------|------|
| futures-collector | [futures-collector.md](./futures-collector.md) |
