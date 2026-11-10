"""MOCK_MODE용 가짜 OpenAI 응답 (테스트 비용 0).

MOCK_SCENARIO:
- normal       : PRD 스키마를 채운 정상 응답
- no_face      : 얼굴 미검출 응답
- invalid_json : JSON이 아닌 응답 (원문 fallback 확인용)
- api_error    : OpenAI 타임아웃 예외 발생 (오류 메시지 확인용)
- xss          : 응답에 HTML/스크립트가 섞인 경우 (escape 확인용)
"""

import json
import time

import httpx2
import openai

from config import get_secret

MOCK_DELAY_SECONDS = 1.5

SAMPLE_RESULT = {
    "face_detected": True,
    "face_shape": "둥글고 균형 잡힌 얼굴형으로, 사람을 편안하게 만드는 원만한 기운이 있습니다.",
    "features": {
        "forehead": "이마가 넓고 반듯해 초년운이 밝고 학업과 배움에 복이 있습니다.",
        "eyebrows": "눈썹이 가지런해 형제·친구와의 인연이 좋고 의리가 있습니다.",
        "eyes": "눈빛이 맑아 총명하고 사람의 마음을 잘 읽습니다.",
        "nose": "콧대가 곧고 콧방울이 도톰해 재물을 모으는 힘이 있는 복코입니다.",
        "mouth": "입꼬리가 살짝 올라가 말년까지 웃을 일이 많은 상입니다.",
        "ears": "귀가 두툼해 복을 잘 듣고 받아들이는 상입니다.",
        "chin": "턱선이 단단해 말년운이 안정적이고 아랫사람 복이 있습니다.",
    },
    "overall": "전체적으로 조화로운 상으로, 꾸준히 노력하면 중년 이후 크게 빛을 보는 대기만성형입니다.",
    "fortune": {
        "wealth": "큰돈보다 꾸준히 쌓이는 재물운이 강합니다.",
        "love": "진심이 통하는 인연을 만나기 쉬운 시기입니다.",
        "career": "사람을 이끄는 자리에서 능력을 발휘합니다.",
        "health": "규칙적인 수면과 산책이 운을 더 밝혀줍니다.",
    },
    "score": 87,
    "advice": "지금처럼 웃는 얼굴을 유지하면 복이 저절로 따라옵니다.",
    "keywords": ["#복코", "#대기만성", "#리더형"],
}

NO_FACE_RESULT = {
    "face_detected": False,
    "face_shape": "",
    "features": {},
    "overall": "",
    "fortune": {},
    "score": 0,
    "advice": "",
    "keywords": [],
}

INVALID_JSON_TEXT = "관상을 살펴보니 아주 좋은 상입니다! (JSON 형식이 아닌 응답 예시)"


def mock_completion(style: str) -> tuple[str, str | None]:
    """시나리오에 맞는 (응답 문자열, refusal) 튜플을 반환하거나 예외를 발생시킨다."""
    time.sleep(MOCK_DELAY_SECONDS)
    scenario = (get_secret("MOCK_SCENARIO", "normal") or "normal").strip().lower()

    if scenario == "no_face":
        return json.dumps(NO_FACE_RESULT, ensure_ascii=False), None
    if scenario == "invalid_json":
        return INVALID_JSON_TEXT, None
    if scenario == "api_error":
        request = httpx2.Request("POST", "https://api.openai.com/v1/chat/completions")
        raise openai.APITimeoutError(request=request)

    if scenario == "xss":
        payload = '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>'
        result = dict(SAMPLE_RESULT, overall=payload, keywords=["<b>#굵게</b>"], advice=payload)
        return json.dumps(result, ensure_ascii=False), None

    result = dict(SAMPLE_RESULT, overall=f"[{style}] {SAMPLE_RESULT['overall']}")
    return json.dumps(result, ensure_ascii=False), None
