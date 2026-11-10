"""설정/비밀 값 로딩: st.secrets(Streamlit Cloud) → 환경 변수(.env) 순으로 조회."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gpt-4o"
DEFAULT_MAX_REQUESTS = 10
DEFAULT_MAX_REQUESTS_PER_DAY = 300
MAX_UPLOAD_MB = 10


def get_secret(key: str, default: str | None = None) -> str | None:
    """st.secrets에서 먼저 찾고, 없으면 환경 변수(.env 포함)에서 찾는다."""
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        # 로컬에 .streamlit/secrets.toml이 없으면 st.secrets 접근 시 예외가 발생한다.
        pass
    value = os.getenv(key)
    return value if value else default


def get_bool(key: str, default: bool = False) -> bool:
    """'true/1/yes/on' 형태의 설정 값을 bool로 읽는다."""
    value = get_secret(key)
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "on"}


def get_int(key: str, default: int) -> int:
    """정수 설정 값을 읽는다. 값이 없거나 잘못되면 default."""
    try:
        return int(get_secret(key, str(default)))
    except (TypeError, ValueError):
        return default


def is_mock_mode() -> bool:
    """MOCK_MODE=true 이면 OpenAI 대신 샘플 응답을 사용한다 (테스트용)."""
    return get_bool("MOCK_MODE")


def max_requests_per_session() -> int:
    """세션당 허용되는 실제 분석 요청 횟수."""
    return max(0, get_int("MAX_REQUESTS_PER_SESSION", DEFAULT_MAX_REQUESTS))


def max_requests_per_day() -> int:
    """앱 전체(모든 사용자 합산)에서 하루(UTC)에 허용되는 실제 분석 요청 횟수."""
    return max(0, get_int("MAX_REQUESTS_PER_DAY", DEFAULT_MAX_REQUESTS_PER_DAY))
