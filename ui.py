"""결과 화면 HTML 조각 생성. 모델 응답은 반드시 html.escape 후 삽입한다 (XSS 방지)."""

from html import escape
from typing import Any

import streamlit as st

from report import DISCLAIMER, FEATURE_LABELS, FORTUNE_LABELS
from ui_styles import CSS

FEATURE_ICONS = {
    "face_shape": "🌕",
    "forehead": "🌄",
    "eyebrows": "〰️",
    "eyes": "👁️",
    "nose": "👃",
    "mouth": "👄",
    "ears": "👂",
    "chin": "🗿",
}
FORTUNE_ICONS = {"wealth": "💰", "love": "💞", "career": "💼", "health": "🍀"}
EMPTY_TEXT = "관상가가 이 부분은 말을 아꼈습니다."


def _html(markup: str) -> None:
    """HTML 조각을 렌더링한다 (호출 전 사용자/모델 데이터는 이미 escape 되어 있어야 함)."""
    st.markdown(markup, unsafe_allow_html=True)


def _card(title: str, body: str, extra_class: str = "") -> str:
    """제목/본문을 escape 해서 카드 HTML을 만든다."""
    return (
        f'<div class="gs-card {extra_class}"><h4>{escape(title)}</h4>'
        f"<p>{escape(body or EMPTY_TEXT)}</p></div>"
    )


def inject_css() -> None:
    """커스텀 CSS를 페이지에 주입한다."""
    _html(CSS)


def render_header() -> None:
    """앱 제목, 소개, 이용 방법 3단계."""
    _html(
        """
<div class="gs-header">
  <h1>🔮 AI 관상가</h1>
  <p class="gs-sub">얼굴 사진 한 장이면, AI 관상가가 재미로 당신의 상(相)을 풀어드립니다.</p>
  <ul class="gs-steps">
    <li><b>①</b>사진 올리기</li>
    <li><b>②</b>관상 스타일 고르기</li>
    <li><b>③</b>관상 보기</li>
  </ul>
</div>
"""
    )


def render_footer() -> None:
    """하단 면책 문구."""
    _html(f'<div class="gs-footer">⚠️ {escape(DISCLAIMER)}</div>')


def render_reading(result: dict[str, Any], style: str) -> None:
    """정규화된 관상 결과를 점수 → 종합 → 부위별 → 운세 → 조언 순으로 렌더링한다."""
    score = result.get("score")
    keywords = "".join(f'<span class="gs-chip">{escape(k)}</span>' for k in result.get("keywords", []))
    if score is not None:
        score_html = (
            f'<p class="gs-score">{score}<small>점</small></p>'
            f'<div class="gs-bar" role="progressbar" aria-valuenow="{score}" aria-valuemin="0" '
            f'aria-valuemax="100"><span style="width:{score}%"></span></div>'
        )
    else:
        score_html = '<p class="gs-score">?</p>'
    _html(
        f'<div class="gs-hero"><p class="gs-label">{escape(style)}가 본 관상 점수</p>'
        f'{score_html}<div class="gs-chips">{keywords}</div></div>'
    )

    _html('<div class="gs-section">📜 종합 관상</div>')
    _html(_card("한마디로 말하자면", result.get("overall", ""), "gs-overall"))

    features = result.get("features", {})
    cards = [_card(f"{FEATURE_ICONS['face_shape']} 얼굴형", result.get("face_shape", ""), "gs-feature")]
    cards += [
        _card(f"{FEATURE_ICONS[key]} {label}", features.get(key, ""), "gs-feature")
        for key, label in FEATURE_LABELS.items()
    ]
    _html('<div class="gs-section">🧭 부위별 풀이</div>')
    _html(f'<div class="gs-grid">{"".join(cards)}</div>')

    fortune = result.get("fortune", {})
    cards = [
        _card(f"{FORTUNE_ICONS[key]} {label}", fortune.get(key, ""))
        for key, label in FORTUNE_LABELS.items()
    ]
    _html('<div class="gs-section">🌟 운세</div>')
    _html(f'<div class="gs-grid">{"".join(cards)}</div>')

    if result.get("advice"):
        _html(
            f'<div class="gs-advice"><p>{escape(result["advice"])}</p>'
            f'<span class="gs-by">— 관상가의 한마디</span></div>'
        )
