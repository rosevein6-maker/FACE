"""AI 관상가 — Streamlit 진입점."""

import hashlib
import io
import logging
import threading
import warnings
from datetime import datetime, timezone

import streamlit as st
from PIL import Image, UnidentifiedImageError

from config import (
    MAX_UPLOAD_MB,
    get_secret,
    is_mock_mode,
    max_requests_per_day,
    max_requests_per_session,
)
from face_reader import (
    STATUS_NO_FACE,
    STATUS_OK,
    STATUS_PARSE_ERROR,
    STATUS_REFUSED,
    FaceReadingError,
    read_face,
)
from image_utils import MAX_PIXELS, ImageTooLargeError, check_pixels, prepare_image
from prompts import DEFAULT_STYLE, STYLES
from report import DISCLAIMER, format_result_text
from ui import inject_css, render_footer, render_header, render_reading

logging.basicConfig(level=logging.INFO)

ALLOWED_TYPES = ["jpg", "jpeg", "png", "webp"]
PRIVACY_NOTICE = "업로드한 사진은 저장되지 않으며, 관상 분석을 위해 OpenAI API로만 전송됩니다."

st.set_page_config(page_title="AI 관상가", page_icon="🔮", layout="centered")


def init_state() -> None:
    """세션 상태 기본값을 설정한다."""
    st.session_state.setdefault("request_count", 0)
    st.session_state.setdefault("cache", {})  # (이미지 해시, 스타일) → 결과
    st.session_state.setdefault("current", None)  # {"result", "style"}
    st.session_state.setdefault("error", None)
    st.session_state.setdefault("input_version", 0)  # 올리면 업로더/카메라가 초기화된다


def reset() -> None:
    """'다른 사진으로 다시 보기': 결과와 입력 위젯을 비운다 (캐시·횟수는 유지)."""
    st.session_state.current = None
    st.session_state.error = None
    st.session_state.input_version += 1


@st.cache_resource
def _daily_usage() -> dict:
    """앱 전체(모든 세션 공유)의 하루 요청 수. 새로고침으로 세션 제한을 우회해도 비용 상한을 지킨다."""
    return {"date": None, "count": 0, "lock": threading.Lock()}


def reserve_daily_request() -> bool:
    """앱 전체 일일 한도 안이면 1회를 차감하고 True, 소진됐으면 False."""
    usage = _daily_usage()
    today = datetime.now(timezone.utc).date()
    with usage["lock"]:
        if usage["date"] != today:
            usage["date"], usage["count"] = today, 0
        if usage["count"] >= max_requests_per_day():
            return False
        usage["count"] += 1
        return True


def remaining_requests() -> int:
    """이번 세션에서 남은 분석 횟수."""
    return max(0, max_requests_per_session() - st.session_state.request_count)


def analyze(image_bytes: bytes, style: str) -> None:
    """캐시 확인 → 횟수 제한 → 분석 → 결과를 session_state에 저장한다 (입력 검증은 validate_image)."""
    st.session_state.error = None
    st.session_state.current = None

    cache_key = (hashlib.sha256(image_bytes).hexdigest(), style)
    if cache_key in st.session_state.cache:
        st.session_state.current = {"result": st.session_state.cache[cache_key], "style": style}
        return

    if remaining_requests() <= 0:
        st.session_state.error = "이번 세션의 분석 횟수를 모두 사용했습니다. 잠시 후 새로고침해서 다시 이용해주세요."
        return

    try:
        data_url = prepare_image(io.BytesIO(image_bytes))
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        st.session_state.error = "이미지를 열 수 없습니다. 손상되지 않은 jpg, png, webp 사진을 올려주세요."
        return

    if not reserve_daily_request():
        st.session_state.error = "오늘 준비된 관상 풀이가 모두 소진되었습니다. 내일 다시 찾아주세요."
        return

    st.session_state.request_count += 1
    try:
        with st.spinner("🔮 관상가가 얼굴을 찬찬히 살펴보는 중입니다..."):
            result = read_face(data_url, style)
    except FaceReadingError as exc:
        st.session_state.error = exc.user_message
        return

    if result["status"] in (STATUS_OK, STATUS_NO_FACE):
        st.session_state.cache[cache_key] = result
    st.session_state.current = {"result": result, "style": style}


def validate_image(image_bytes: bytes) -> str | None:
    """크기 초과/손상 이미지면 사용자 안내 메시지를, 정상이면 None을 반환한다."""
    if len(image_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
        return f"파일이 너무 큽니다. {MAX_UPLOAD_MB}MB 이하의 사진을 올려주세요."
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)  # 아래에서 직접 판단
            with Image.open(io.BytesIO(image_bytes)) as image:
                check_pixels(image)
                image.verify()
    except (ImageTooLargeError, Image.DecompressionBombError):
        return f"사진 해상도가 너무 큽니다. {MAX_PIXELS // 10_000:,}만 화소 이하의 사진을 올려주세요."
    except (UnidentifiedImageError, OSError, ValueError):
        return "이미지를 열 수 없습니다. 손상되지 않은 jpg, png, webp 사진을 올려주세요."
    return None


def render_input(source, key: str, style: str) -> None:
    """업로드/카메라 입력 하나를 검증 → 미리보기 → 분석 버튼으로 렌더링한다."""
    if source is None:
        return
    image_bytes = source.getvalue()
    error = validate_image(image_bytes)
    if error:
        st.error(f"🙏 {error}")
        return
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.image(image_bytes, caption="관상을 볼 사진", width=280)
    if st.button("🔮 관상 보기", type="primary", key=f"analyze_{key}", width="stretch"):
        analyze(image_bytes, style)


def render_result() -> None:
    """session_state에 저장된 결과/오류를 표시한다 (rerun 후에도 유지)."""
    if st.session_state.error:
        st.error(f"🙏 {st.session_state.error}")
        return

    current = st.session_state.current
    if not current:
        return
    result, style = current["result"], current["style"]
    status = result["status"]

    if status == STATUS_NO_FACE:
        st.warning("👀 관상가가 얼굴을 찾지 못했습니다. 얼굴이 잘 보이는 정면 사진을 올려주세요.")
    elif status == STATUS_REFUSED:
        st.warning("🙇 이 사진으로는 관상을 봐드리기 어렵습니다. 다른 정면 사진으로 다시 시도해주세요.")
    elif status == STATUS_PARSE_ERROR:
        st.info("📜 풀이를 정리하지 못해 관상가의 말을 그대로 옮겨드립니다.")
        st.text(result.get("raw_text") or "(관상가가 아무 말도 하지 않았습니다)")
    else:
        render_reading(result, style)
        download_col, retry_col = st.columns(2)
        with download_col:
            st.download_button(
                "📥 결과 저장하기 (.txt)",
                data=format_result_text(result, style).encode("utf-8"),
                file_name="관상_결과.txt",
                mime="text/plain",
                width="stretch",
            )
        with retry_col:
            st.button("🔄 다른 사진으로 다시 보기", on_click=reset, width="stretch", key="retry")
        return

    st.button("🔄 다른 사진으로 다시 보기", on_click=reset, key="retry")


init_state()
inject_css()

if not is_mock_mode() and not get_secret("OPENAI_API_KEY"):
    render_header()
    st.error("🔑 OPENAI_API_KEY가 설정되지 않았습니다. 로컬은 .env, Streamlit Cloud는 Secrets에 등록해주세요.")
    st.stop()

with st.sidebar:
    st.header("⚙️ 설정")
    style = st.radio(
        "관상 스타일",
        list(STYLES),
        index=list(STYLES).index(DEFAULT_STYLE),
        captions=["점잖고 품위 있게", "웃음 가득 예능처럼", "핵심만 단호하게"],
    )
    remaining_slot = st.empty()  # 분석 후 값을 채우기 위해 자리만 잡아둔다
    st.divider()
    st.caption(f"🔒 {PRIVACY_NOTICE}")
    st.caption(f"⚠️ {DISCLAIMER}")

render_header()

version = st.session_state.input_version
upload_tab, camera_tab = st.tabs(["📷 사진 업로드", "🤳 카메라 촬영"])
with upload_tab:
    uploaded = st.file_uploader(
        "얼굴이 잘 보이는 정면 사진을 올려주세요 (jpg, png, webp · 최대 10MB)",
        type=ALLOWED_TYPES,
        key=f"uploader_{version}",
    )
    render_input(uploaded, "upload", style)
with camera_tab:
    shot = st.camera_input("정면을 바라보고 촬영해주세요", key=f"camera_{version}")
    render_input(shot, "camera", style)

render_result()

remaining = remaining_requests()
remaining_slot.metric("남은 분석 횟수", f"{remaining} / {max_requests_per_session()}")
render_footer()
