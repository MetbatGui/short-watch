# Troubleshooting Index

> 실제로 부딪힌 문제와 해결 과정 기록. ADR이 "왜 이렇게 설계했나"라면, 이건 "이거 하다가 뭐가 터졌고 어떻게 고쳤나"다.
> ADR과 동일한 파일 구조를 쓴다: 이 README는 인덱스, 개별 사례는 `YYYY-MM-DD-{slug}.md`.

---

## 언제 쓰나

- 원인 파악에 시간이 걸린 버그/장애를 고쳤을 때
- 외부 API/데이터 소스가 예상과 다르게 동작해서 우회하거나 설계를 바꿨을 때
- 같은 실수를 반복하지 않기 위해 남겨야 하는 것

**Not 대상**: 바로 원인 파악되는 사소한 오타/typo, 커밋 메시지만으로 충분한 것.

---

## 파일 규칙

**위치**: `docs/troubleshooting/YYYY-MM-DD-{slug}.md`
**slug 규칙**: kebab-case, 문제를 짧게 요약

## 기록 형식

```markdown
# {제목}

**Date**: YYYY-MM-DD

## 증상
무엇이 어떻게 잘못됐나

## 원인
왜 그랬나

## 해결
어떻게 고쳤나

## 참고
관련 ADR/링크 (있으면)
```

---

## GitHub Issue 미러

저장소(markdown 파일)가 SSOT. GitHub Issue는 이를 외부에 노출하는 미러다.

- 파일 생성 시 `troubleshooting` 라벨을 단 Issue를 하나 만든다. 본문에는 요약 + 파일 링크만 두고, 전문은 복사하지 않는다.
- 파일 내용이 갱신되면 대응 Issue도 함께 갱신한다.

## 목록

| Date | 제목 | 요약 |
|------|------|------|
| {{YYYY-MM-DD}} | [{{slug}}](./{{YYYY-MM-DD-slug}}.md) | {{한줄요약}} |
