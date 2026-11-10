"""관상 결과를 다운로드용 텍스트로 변환."""

from datetime import datetime
from typing import Any

FEATURE_LABELS = {
    "forehead": "이마",
    "eyebrows": "눈썹",
    "eyes": "눈",
    "nose": "코",
    "mouth": "입",
    "ears": "귀",
    "chin": "턱",
}
FORTUNE_LABELS = {
    "wealth": "재물운",
    "love": "애정운",
    "career": "직업운",
    "health": "건강운",
}
DISCLAIMER = "본 결과는 재미를 위한 AI 콘텐츠이며 과학적 근거가 없습니다."


def format_result_text(result: dict[str, Any], style: str) -> str:
    """정규화된 결과 dict를 사람이 읽기 좋은 텍스트로 만든다."""
    lines = [
        "AI 관상가 결과",
        f"스타일: {style}",
        f"일시: {datetime.now():%Y-%m-%d %H:%M}",
        "=" * 40,
    ]
    if result.get("score") is not None:
        lines.append(f"관상 점수: {result['score']}점")
    if result.get("keywords"):
        lines.append(f"키워드: {' '.join(result['keywords'])}")

    lines += ["", "[종합 관상]", result.get("overall", ""), "", "[얼굴형]", result.get("face_shape", ""), ""]
    lines.append("[부위별 풀이]")
    for key, label in FEATURE_LABELS.items():
        lines.append(f"- {label}: {result.get('features', {}).get(key, '')}")

    lines += ["", "[운세]"]
    for key, label in FORTUNE_LABELS.items():
        lines.append(f"- {label}: {result.get('fortune', {}).get(key, '')}")

    lines += ["", "[조언]", result.get("advice", ""), "", "-" * 40, DISCLAIMER]
    return "\n".join(lines) + "\n"
