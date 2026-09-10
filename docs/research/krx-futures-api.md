# KRX 선물 일별매매정보 API 학습

## 핵심 발견

`https://data.krx.co.kr/comm/bldAttendant/executeDynamicReport.cmd` 아니라 **`https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd`**가 실제 JSON 데이터 반환 엔드포인트다. `executeDynamicReport.cmd`는 (파라미터/세션 무관하게) 항상 "서비스 에러 - 입력된 값이 유효한 값인지 확인" HTML 에러페이지를 반환한다. 이건 ceiling-tracker(`src/infrastructure/krx_adapter.py`)에서 이미 검증된 패턴.

## 로그인 (세션 획득)

1. `GET /contents/MDC/COMS/client/MDCCOMS001.cmd` — 초기 JSESSIONID 발급
2. `GET /contents/MDC/COMS/client/view/login.jsp?site=mdc` (Referer: 1번 URL)
3. `POST /contents/MDC/COMS/client/MDCCOMS001D1.cmd` — `{mbrNm:"", telNo:"", di:"", certType:"", mbrId, pw}`
   - 응답 JSON `_error_code`: `CD001` = 성공, `CD011` = 중복로그인(→ `skipDup: "Y"` 추가 후 재전송)
4. 로그인 후 쿠키 수동 세팅: `mdc.client_session=true`, `lang=ko_KR` (domain=data.krx.co.kr)

로그인 없이도 되는 bld가 있을 수 있으나(예: 개별주 시세), 이번 검증에선 로그인 세션으로 호출.

## 선물 일별매매정보 호출

**Endpoint**: `POST https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd`

**Headers**:
```
Accept: application/json, text/javascript, */*; q=0.01
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Origin: https://data.krx.co.kr
Referer: https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201
X-Requested-With: XMLHttpRequest
```

**Params (코스피200 선물)**:
```
bld=dbms/MDC/STAT/standard/MDCSTAT12501
locale=ko_KR
trdDd=20260910          # 조회일 (YYYYMMDD)
prodId=KR___FUK2I       # 코스피200 선물 상품군 코드
trdDdBox1=20260910      # trdDd와 동일값 (날짜선택 UI 잔재로 추정)
aggBasTpCd=             # 빈 문자열 그대로 전송
rghtTpCd=T
share=1
money=3
csvxls_isNo=false
```

## Response 구조

```json
{
  "output": [
    {
      "ISU_CD": "KR4A01690002",
      "ISU_SRT_CD": "A0169000",
      "ISU_NM": "코스피200 F 202609 (야간)",
      "TDD_CLSPRC": "1,113.30",
      "FLUC_TP_CD": "2",
      "CMPPREVDD_PRC": "-3.90",
      "TDD_OPNPRC": "1,117.25",
      "TDD_HGPRC": "1,126.50",
      "TDD_LWPRC": "1,099.95",
      "SPOT_PRC": "1,112.13",
      "SETL_PRC": "0.00",
      "ACC_TRDVOL": "22,588",
      "ACC_TRDVAL": "6,274,306,412,500",
      "ACC_OPNINT_QTY": "65,826",
      "SECUGRP_ID": "FU"
    }
  ],
  "CURRENT_DATETIME": "..."
}
```

**필드 설명**:
- `ISU_NM`: 종목명. **"(야간)"/"(주간)" 문자열로 야간선물/정규장선물 구분됨** — 한 응답에 둘 다 섞여서 나옴, 별도 API 없음
- `TDD_CLSPRC`: 종가, `TDD_OPNPRC`/`TDD_HGPRC`/`TDD_LWPRC`: 시/고/저가
- `CMPPREVDD_PRC`: 전일대비
- `SPOT_PRC`: 현물(기초자산) 가격
- `SETL_PRC`: 정산가 (야간선물 행은 대부분 "0.00" — 아직 정산 전이거나 야간선물엔 정산가 개념이 다르게 적용되는 듯, 추가 확인 필요)
- `ACC_TRDVOL`: 누적거래량, `ACC_TRDVAL`: 누적거래대금
- **`ACC_OPNINT_QTY`: 미결제약정수량** — 옵션 Max Pain 계산에도 이 필드명 패턴이 재사용될 가능성 높음
- `SECUGRP_ID`: "FU" (선물)

**Edge case**:
- 숫자 필드가 전부 문자열이고 천단위 콤마(`,`) 포함 — `float(x.replace(',', ''))` 파싱 필요
- 미거래 데이터는 `"-"` 문자열로 옴 (예: `TDD_CLSPRC: "-"`)
- 만기 근월물 등 일부 종목은 `ACC_OPNINT_QTY`도 `"-"`로 옴

## Spec 반영 체크리스트

- [x] API Endpoint: `POST /comm/bldAttendant/getJsonData.cmd`
- [x] 파라미터: 위 목록
- [x] Response 구조: `output` 배열, 필드 15개
- [x] Edge case: 콤마 포함 숫자문자열, `"-"` 결측치
- [x] 외부 dependency: `requests` (session 기반 로그인 필요)
