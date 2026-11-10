# AI 관상가

얼굴 사진을 업로드하면 OpenAI 이미지 분석 모델이 재미로 관상을 봐주는 Streamlit 앱입니다.
요구사항은 [prd.md](prd.md)를 참고하세요.

> 본 결과는 재미를 위한 AI 콘텐츠이며 과학적 근거가 없습니다.

## 로컬 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell/cmd)
# source .venv/bin/activate     # macOS/Linux

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경 변수 설정: .env.example을 복사해 .env를 만들고 키 입력
copy .env.example .env          # macOS/Linux: cp .env.example .env

# 4. 실행
streamlit run app.py
```

## 환경 변수

| 이름 | 설명 | 기본값 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API 키 (필수) | — |
| `OPENAI_MODEL` | 이미지 입력을 지원하는 OpenAI 모델 | `gpt-4o` |
| `MAX_REQUESTS_PER_SESSION` | 세션당 실제 분석 요청 허용 횟수 (같은 사진+스타일 재요청은 캐시라 차감 안 됨) | `10` |
| `MAX_REQUESTS_PER_DAY` | 앱 전체(모든 사용자 합산) 하루(UTC) 분석 상한. 새로고침으로 세션 제한을 우회해도 비용 상한 유지 | `300` |
| `MOCK_MODE` | `true`면 OpenAI를 호출하지 않고 샘플 응답 사용 (테스트용, 비용 0) | `false` |
| `MOCK_SCENARIO` | MOCK_MODE 시나리오: `normal` / `no_face` / `invalid_json` / `api_error` / `xss` | `normal` |

### 테스트용 MOCK 모드 실행

```bash
# PowerShell
$env:MOCK_MODE="true"; $env:MOCK_SCENARIO="no_face"; streamlit run app.py
# Git Bash / macOS / Linux
MOCK_MODE=true MOCK_SCENARIO=no_face streamlit run app.py
```

> 배포 환경(Streamlit Cloud Secrets)에는 `MOCK_MODE`를 넣지 마세요.

Streamlit Cloud에는 `.env`가 올라가지 않습니다. 배포 시 **App settings → Secrets**에 같은 키를 TOML 형식으로 등록하세요.

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o"
```

## 테스트

Playwright E2E + 단위 테스트. 앱을 `MOCK_MODE=true`와 더미 API 키로 자동 실행하므로 OpenAI 비용이 들지 않습니다.

```bash
pip install -r requirements-dev.txt
playwright install chromium

pytest                                                        # 전체 (약 2분)
pytest tests/test_units.py                                    # 단위 테스트만 (빠름)
pytest tests/test_e2e.py::test_normal_flow_shows_full_reading # 단일 테스트
```

- 테스트 이미지(`tests/fixtures/`)는 자동 생성되고, 스크린샷은 `tests/screenshots/`에 저장됩니다 (둘 다 git 제외).
- 검토 결과는 [review_report.md](review_report.md) 참고.

## 배포 (Streamlit Community Cloud)

1. GitHub에 push (`.env`가 커밋되지 않았는지 `git status`로 확인)
2. share.streamlit.io → 저장소 선택 → Main file `app.py`
3. Advanced settings → Python 3.12 이상 선택, Secrets에 `OPENAI_API_KEY`, `OPENAI_MODEL`(선택), `MAX_REQUESTS_PER_DAY`(선택) 등록 — `MOCK_MODE`는 넣지 않음
4. OpenAI 대시보드에서 월 사용 한도 설정
