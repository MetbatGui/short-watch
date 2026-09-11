# futures-collector Spec

## 개요

KOSPI200 선물 일별매매정보(KRX 응답 원본, 모든 계약월/세션 포함)를 KRX Data Marketplace에서 수집해 **가공 없이 그대로(Bronze)** Parquet으로 저장한다. cronjob이 하루 2번(야간마감 후, 정규장마감 후) CLI를 실행해서 수집한다.

## 설계 원칙: Bronze — 원본 그대로, 변환 없음

- KRX 응답의 필드명(`TDD_CLSPRC`, `ISU_NM` 등), 문자열 그대로("1,113.30", "-" 포함)를 **가공하지 않고** 저장한다.
- 콤마 제거, 타입 변환("-"→null), 필드명 변경, 근월/차월 선택, 세션(주간/야간) 구분 — 이런 가공은 전부 **이 Slice의 범위 밖**이다. Bronze를 읽어서 가공하는 건 나중(Silver/Gold, Bear Score 등 다른 Slice)의 책임이다.
- 이 Slice에 Domain 모델이 없다 — 파싱/검증할 게 없으니 Domain 계층 자체가 필요 없다.

## 입력/출력

**입력**: 없음(CLI 인자로 대상일자 생략 가능 — 생략 시 KST 기준 오늘 날짜 사용). 필요시 `--date YYYYMMDD`로 특정일 재수집 가능.

**출력**: 대상일자에 KRX가 반환한 선물 일별매매정보 응답의 `output` 배열 **전체**(모든 계약월, 모든 세션, 스프레드 포함 — 필터링 없음)가 Parquet 파일에 원본 그대로 저장됨. 날짜는 파일 경로(파티션)로 구분하고, 행 내부 데이터는 건드리지 않는다.

## 데이터 소스 (스파이크로 확인됨)

- Endpoint: `POST https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd`
- 로그인 필요 (KRX_USERNAME/KRX_PASSWORD 환경변수)
- bld: `dbms/MDC/STAT/standard/MDCSTAT12501`, prodId: `KR___FUK2I` (코스피200 선물)
- 참고: `spikes/krx-futures/findings.md` (승인 후 `docs/research/`로 정제 예정)

## Acceptance Criteria

### 정입력 케이스

- 대상일자에 데이터가 존재하면(`output` 배열이 비어있지 않으면), 그 배열을 그대로 Parquet에 저장한다. 행 개수·필드·값 어느 것도 가공하지 않는다.
- 같은 날짜로 재실행 시 기존 Parquet 파일을 덮어쓴다 — 중복 append 하지 않는다.

### 오류/예외 케이스

- 대상일자가 휴장일이거나 데이터가 없으면(`output`이 빈 배열), 실패로 취급하지 않고 정상 종료한다(exit 0, JSON `code: OK_NO_DATA`).
- 로그인 실패(KRX_USERNAME/PASSWORD 누락 또는 인증 실패) 시 즉시 종료한다(재시도 안 함). exit 1, `code: ERR_LOGIN_FAILED`.
- KRX 서버 네트워크 오류/타임아웃 시 지수백오프로 최대 3회 재시도 후 실패 처리한다. exit 1, `code: ERR_NETWORK_RETRY_EXHAUSTED`.

### CLI 출력 (ddd.md "CLI Presentation 규약" 참고)

- exit code는 `0`(성공)/`1`(실패)만 쓴다.
- 결과는 구조화된 JSON으로 stdout 출력한다: `{"status": "ok"|"error", "code": "OK_COLLECTED"|"OK_NO_DATA"|"ERR_LOGIN_FAILED"|"ERR_NETWORK_RETRY_EXHAUSTED", "records": N, "message": "..."}` (`records`는 저장된 원본 행 개수 전체)
- 테스트는 Typer `CliRunner`로 검증한다 (`result.exit_code` + `json.loads(result.output)["code"]`).

## 스케줄 (참고, cron 설정은 별도)

- 야간마감(KST 06:00) 이후 **06:10** 실행 — 스파이크로 확정(06:07 시점 이미 거래량 고정 확인됨)
- 정규장마감(KST 15:40 추정) 이후 **15:50** 실행 — 15:03~15:07 구간까지 거래중 확인, 17:30엔 고정 확인. 정확한 멈춤 시점은 15:07~17:28 사이 공백으로 미확정. 다음 장중 15:35~15:45 구간 직접 재검증 필요

## 설계 경계 (이 Slice 밖)

- 필드 파싱/타입변환, 근월·차월 선택, 세션 구분, 정산가 해석 — 전부 Bronze→Silver 단계(별도 Slice)
- 옵션/공매도 데이터 수집은 별도 Slice
- Bear Score 계산은 이 Slice 범위 밖
- 야간선물 실시간 조회, 표시(프론트엔드)는 범위 밖
