import pytest

from fakes import FakeResponse, FakeSession


@pytest.fixture
def sample_rows() -> list[dict]:
    """스파이크로 확보한 실제 KRX 응답 일부 (spikes/krx-futures/findings.md 기반)."""
    return [
        {
            "ISU_CD": "KR4A016C0004",
            "ISU_SRT_CD": "A016C000",
            "ISU_NM": "코스피200 F 202612 (야간)",
            "TDD_CLSPRC": "1,073.00",
            "CMPPREVDD_PRC": "-39.00",
            "ACC_TRDVOL": "24,309",
            "ACC_OPNINT_QTY": "128,759",
            "SETL_PRC": "0.00",
        },
        {
            "ISU_CD": "KR4A016C0004",
            "ISU_SRT_CD": "A016C000",
            "ISU_NM": "코스피200 F 202612 (주간)",
            "TDD_CLSPRC": "1,088.30",
            "CMPPREVDD_PRC": "-23.70",
            "ACC_TRDVOL": "104,371",
            "ACC_OPNINT_QTY": "127,733",
            "SETL_PRC": "0.00",
        },
    ]


@pytest.fixture
def login_success_response() -> FakeResponse:
    return FakeResponse(data={"_error_code": "CD001", "MBR_NO": "1000005836"})


@pytest.fixture
def login_failure_response() -> FakeResponse:
    return FakeResponse(data={"_error_code": "CD999"})


@pytest.fixture
def no_op_sleep():
    return lambda seconds: None


@pytest.fixture
def make_session():
    """로그인 GET 2회(성공)를 자동으로 앞에 채워주는 FakeSession 생성 팩토리.

    _login()이 매번 GET을 2번 먼저 호출하는 걸 테스트마다 반복 안 하려고 뽑음.
    로그인 GET 자체가 실패하는 경로를 테스트할 땐 이 팩토리를 쓰지 않고
    FakeSession을 직접 만든다.
    """

    def _make(*post_login_items) -> FakeSession:
        return FakeSession([FakeResponse(), FakeResponse(), *post_login_items])

    return _make
