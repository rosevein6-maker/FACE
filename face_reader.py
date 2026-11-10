"""OpenAI Vision 모델 호출, 오류 변환, 응답 파싱/정규화."""

import json
import logging
from typing import Any

import openai
from openai import OpenAI

from config import DEFAULT_MODEL, get_secret, is_mock_mode
from prompts import DEFAULT_STYLE, USER_PROMPT, build_system_prompt

logger = logging.getLogger(__name__)

MAX_COMPLETION_TOKENS = 1500
REQUEST_TIMEOUT = 60  # 초

FEATURE_KEYS = ["forehead", "eyebrows", "eyes", "nose", "mouth", "ears", "chin"]
FORTUNE_KEYS = ["wealth", "love", "career", "health"]

# 결과 상태
STATUS_OK = "ok"
STATUS_NO_FACE = "no_face"
STATUS_PARSE_ERROR = "parse_error"
STATUS_REFUSED = "refused"


class FaceReadingError(Exception):
    """사용자에게 그대로 보여줄 수 있는 메시지를 담은 분석 오류."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


def get_client() -> OpenAI:
    """API 키로 OpenAI 클라이언트를 만든다."""
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        raise FaceReadingError("OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의해주세요.")
    return OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=1)


def _to_text(value: Any) -> str:
    """None/숫자 등을 안전하게 문자열로 바꾼다."""
    if value is None:
        return ""
    return value.strip() if isinstance(value, str) else str(value)


def _to_score(value: Any) -> int | None:
    """점수를 0~100 정수로 변환한다. 변환할 수 없으면 None."""
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return None


def _to_keywords(value: Any) -> list[str]:
    """keywords를 '#'으로 시작하는 문자열 리스트로 정리한다."""
    if isinstance(value, str):
        value = value.replace(",", " ").split()
    if not isinstance(value, list):
        return []
    keywords = []
    for item in value:
        text = _to_text(item)
        if text:
            keywords.append(text if text.startswith("#") else f"#{text}")
    return keywords


def normalize_result(data: dict[str, Any]) -> dict[str, Any]:
    """모델 JSON의 누락 필드/타입 불일치를 기본값으로 채워 항상 같은 구조로 만든다."""
    features = data.get("features") if isinstance(data.get("features"), dict) else {}
    fortune = data.get("fortune") if isinstance(data.get("fortune"), dict) else {}
    face_detected = data.get("face_detected", True)
    if isinstance(face_detected, str):
        face_detected = face_detected.strip().lower() not in {"false", "0", "no"}

    return {
        "status": STATUS_OK if face_detected else STATUS_NO_FACE,
        "face_shape": _to_text(data.get("face_shape")),
        "features": {key: _to_text(features.get(key)) for key in FEATURE_KEYS},
        "overall": _to_text(data.get("overall")),
        "fortune": {key: _to_text(fortune.get(key)) for key in FORTUNE_KEYS},
        "score": _to_score(data.get("score")),
        "advice": _to_text(data.get("advice")),
        "keywords": _to_keywords(data.get("keywords")),
    }


def parse_response(content: str | None, refusal: str | None = None) -> dict[str, Any]:
    """모델 응답을 정규화된 결과 dict로 변환한다.

    status: ok / no_face / parse_error(raw_text 포함) / refused(raw_text 포함)
    """
    if refusal:
        return {"status": STATUS_REFUSED, "raw_text": refusal}
    try:
        data = json.loads(content or "")
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        return {"status": STATUS_PARSE_ERROR, "raw_text": _to_text(content)}
    return normalize_result(data)


def _call_openai(data_url: str, style: str) -> tuple[str | None, str | None]:
    """OpenAI Vision 모델을 호출해 (content, refusal)을 반환한다."""
    client = get_client()
    response = client.chat.completions.create(
        model=get_secret("OPENAI_MODEL", DEFAULT_MODEL),
        response_format={"type": "json_object"},
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        messages=[
            {"role": "system", "content": build_system_prompt(style)},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "auto"}},
                ],
            },
        ],
    )
    choice = response.choices[0]
    if choice.finish_reason == "content_filter":
        return None, "콘텐츠 정책에 따라 응답이 제한되었습니다."
    if choice.finish_reason == "length":
        # 토큰 한도에서 잘린 JSON(추론 모델이면 빈 응답)을 원문 그대로 보여주지 않는다.
        logger.warning("응답이 max_completion_tokens(%s)에서 잘림", MAX_COMPLETION_TOKENS)
        raise FaceReadingError("관상가의 풀이가 길어져 중간에 끊겼습니다. 다시 한번 시도해주세요.")
    return choice.message.content, choice.message.refusal


def read_face(data_url: str, style: str = DEFAULT_STYLE) -> dict[str, Any]:
    """이미지 data URL로 관상 풀이를 수행한다.

    실패 시 사용자에게 보여줄 메시지를 담은 FaceReadingError를 발생시킨다.
    """
    try:
        if is_mock_mode():
            from mock import mock_completion

            content, refusal = mock_completion(style)
        else:
            content, refusal = _call_openai(data_url, style)
    except FaceReadingError:
        raise
    except openai.AuthenticationError as exc:
        logger.error("OpenAI 인증 실패: %s", exc)
        raise FaceReadingError("OpenAI 인증에 실패했습니다. API 키 설정을 확인해주세요.") from exc
    except openai.RateLimitError as exc:
        logger.warning("OpenAI 요청 한도 초과: %s", exc)
        raise FaceReadingError("지금 요청이 많아 잠시 쉬어가는 중입니다. 잠시 후 다시 시도해주세요.") from exc
    except (openai.APITimeoutError, openai.APIConnectionError) as exc:
        logger.warning("OpenAI 연결/타임아웃 오류: %s", exc)
        raise FaceReadingError("관상가와 연결이 원활하지 않습니다. 잠시 후 다시 시도해주세요.") from exc
    except openai.BadRequestError as exc:
        logger.error("OpenAI 잘못된 요청: %s", exc)
        raise FaceReadingError("이 사진은 분석할 수 없습니다. 다른 사진으로 시도해주세요.") from exc
    except openai.OpenAIError as exc:
        logger.exception("OpenAI 오류")
        raise FaceReadingError("관상 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.") from exc

    return parse_response(content, refusal)
