# 테스트 디렉토리명이 소스 패키지명과 겹쳐서 import 충돌

**Date**: 2026-09-11

## 증상

`futures-collector` Walking Skeleton 구현 중, `future/` 패키지를 만들고 테스트를 `tests/future/test_collect_acceptance.py`에 뒀더니 정상 코드가 다 있는데도 실패함.

```
ModuleNotFoundError: No module named 'future.application'
```

## 원인

pytest 기본 import 방식(prepend)은 테스트 파일 위치에서 `__init__.py`가 있는 폴더를 계속 거슬러 올라가 "패키지 루트"를 찾고, 그 경로를 `sys.path[0]`에 넣은 뒤 폴더명 기반으로 모듈 이름을 붙인다.

`tests/future/__init__.py`가 있으면 pytest가 `tests/`를 `sys.path[0]`에 넣고 `tests/future`를 "future"라는 이름의 패키지로 확정해버린다. Python은 패키지 하나를 찾으면(정규 패키지, `__init__.py` 있음) 다른 `sys.path` 항목에서 같은 이름을 더 찾지 않으므로, 레포 루트의 진짜 `future/` 패키지는 아예 무시된다. `tests/future/`엔 `application` 서브모듈이 없으니 에러가 남.

`testpaths` 설정이나 `--import-mode=importlib`만으로는 해결 안 됨 — 둘 다 시도했지만 `tests/future/__init__.py`가 있는 한 pytest가 여전히 "future"라는 이름으로 그 폴더를 `sys.modules`에 등록해버림.

## 해결

`tests/future/__init__.py`를 삭제(테스트 디렉토리를 패키지로 만들지 않음). 이러면 pytest가 `tests/future/`까지만 rootpath로 잡고, 테스트 모듈이 `future.` 접두사 없이 독립적으로 import돼서 충돌이 사라진다.

```toml
# pyproject.toml — 이것만으로 충분
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

**규칙**: 테스트 서브디렉토리엔 `__init__.py`를 만들지 않는다. 특히 소스 패키지명이랑 겹치는 이름의 테스트 디렉토리를 쓸 땐 더더욱.

## 참고

[docs/plans/futures-collector.md](../plans/futures-collector.md) — Task #7(Walking Skeleton) 구현 중 발견.
