"""커스텀 CSS (한 곳에서 관리). 외부 CDN 없이 동작한다.

색 대비 원칙: 본문/제목 글자는 테마 글자색을 그대로 상속(inherit)하고,
포인트 컬러는 테두리·막대·배경(반투명)에만 써서 라이트/다크 모두에서 읽기 쉽게 한다.
"""

ACCENT_RGB = "200, 85, 61"  # 라이트/다크 양쪽에서 보이는 중간 톤 주홍

CSS = f"""
<style>
/* 본문 폭과 모바일 가로 스크롤 방지 */
.block-container {{ max-width: 860px; padding-top: 2.5rem; }}
.gs-card, .gs-grid, .gs-hero, .gs-advice, .gs-footer {{ box-sizing: border-box; max-width: 100%; }}
.gs-card p, .gs-advice p, .gs-hero p {{ overflow-wrap: anywhere; word-break: keep-all; }}

/* 헤더 */
.gs-header {{ text-align: center; margin-bottom: 1.25rem; }}
.gs-header h1 {{ font-family: serif; font-size: 2.4rem; margin: 0 0 .25rem; letter-spacing: .05em; }}
.gs-header .gs-sub {{ opacity: .8; margin: 0; }}
.gs-steps {{ display: flex; flex-wrap: wrap; justify-content: center; gap: .5rem; margin: 1rem 0 0; padding: 0; list-style: none; }}
.gs-steps li {{
  border: 1px solid rgba({ACCENT_RGB}, .45); border-radius: 999px;
  padding: .3rem .85rem; font-size: .9rem;
}}
.gs-steps b {{ color: inherit; margin-right: .3rem; }}

/* 결과 상단: 점수 + 키워드 */
.gs-hero {{
  text-align: center; padding: 1.5rem 1rem; margin: 1rem 0;
  border: 1px solid rgba({ACCENT_RGB}, .35); border-radius: 1rem;
  background: rgba({ACCENT_RGB}, .07);
}}
.gs-hero .gs-label {{ font-size: .9rem; opacity: .8; margin: 0; }}
.gs-hero .gs-score {{ font-family: serif; font-size: 3.2rem; font-weight: 700; line-height: 1.1; margin: .2rem 0 .6rem; }}
.gs-hero .gs-score small {{ font-size: 1.2rem; font-weight: 400; margin-left: .15rem; }}
.gs-bar {{ height: .55rem; border-radius: 999px; background: rgba(128, 128, 128, .22); overflow: hidden; max-width: 320px; margin: 0 auto 1rem; }}
.gs-bar > span {{ display: block; height: 100%; border-radius: 999px; background: rgb({ACCENT_RGB}); }}
.gs-chips {{ display: flex; flex-wrap: wrap; justify-content: center; gap: .4rem; }}
.gs-chip {{
  padding: .25rem .75rem; border-radius: 999px; font-size: .9rem; font-weight: 600;
  background: rgba({ACCENT_RGB}, .16); border: 1px solid rgba({ACCENT_RGB}, .4);
}}

/* 섹션 제목 */
.gs-section {{ font-family: serif; font-size: 1.3rem; font-weight: 700; margin: 1.75rem 0 .75rem;
  padding-left: .6rem; border-left: 4px solid rgb({ACCENT_RGB}); }}

/* 카드 */
/* 부위 8개·운세 4개가 빈칸 없이 떨어지도록 데스크톱 2열 고정, 모바일 1열 */
.gs-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }}
.gs-card {{
  padding: 1rem 1.1rem; border-radius: .9rem;
  border: 1px solid rgba(128, 128, 128, .28);
  background: rgba(128, 128, 128, .06);
}}
.gs-card h4 {{ margin: 0 0 .4rem; font-size: 1.02rem; font-weight: 700; padding: 0; }}
.gs-card p {{ margin: 0; line-height: 1.65; }}
.gs-card.gs-feature {{ border-left: 4px solid rgb({ACCENT_RGB}); }}
.gs-card.gs-overall {{ border: 1px solid rgba({ACCENT_RGB}, .45); background: rgba({ACCENT_RGB}, .08); }}
.gs-card.gs-overall p {{ font-size: 1.05rem; }}

/* 조언 인용문 */
.gs-advice {{
  margin: 1.25rem 0; padding: 1.1rem 1.3rem; border-radius: .9rem;
  border-left: 5px solid rgb({ACCENT_RGB}); background: rgba({ACCENT_RGB}, .07);
  font-family: serif; font-size: 1.1rem;
}}
.gs-advice p {{ margin: 0; line-height: 1.7; }}
.gs-advice p::before {{ content: "“"; margin-right: .15rem; }}
.gs-advice p::after {{ content: "”"; margin-left: .15rem; }}
.gs-advice .gs-by {{ display: block; text-align: right; font-size: .85rem; opacity: .75; margin-top: .4rem; font-family: sans-serif; }}

/* 푸터 면책 문구 */
.gs-footer {{
  margin-top: 2.5rem; padding: .9rem 0 .5rem; text-align: center; font-size: .85rem; opacity: .75;
  border-top: 1px solid rgba(128, 128, 128, .3);
}}

/* 미리보기 이미지 둥글게 */
[data-testid="stImage"] img {{ border-radius: .75rem; }}

@media (max-width: 640px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; padding-top: 1.5rem; }}
  .gs-header h1 {{ font-size: 1.9rem; }}
  .gs-hero .gs-score {{ font-size: 2.6rem; }}
  .gs-grid {{ grid-template-columns: 1fr; }}
}}
</style>
"""
