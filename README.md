# 희소식 (heesosik.news)

지칠 때 열어 보는 좋은 소식. 전 세계의 좋은 소식만 골라 매일 한국어로 전합니다.

## 구조
- `issues/N.json` — 각 호의 원고 (1호, 2호, …)
- `build.py` — JSON을 읽어 `index.html`(최신 호), `issues/N.html`, `archive.html`, `sitemap.xml`을 만든다
- `assets/` — 공용 스타일과 스크립트

## 새 호 발행
1. `issues/` 에 다음 번호의 JSON 추가 (1.json 형식 그대로)
2. `python3 build.py`
3. 커밋 후 main에 push → Netlify가 자동 배포

## 편집 원칙
- 하루 머리기사 1 + 기사 5개
- 구성: 🇰🇷 국내 훈훈한 소식 2~3개, 🐾 반려동물·동물 소식 1개 이상, 🌍 해외 감동 사연 1~2개, 숫자형 소식은 0~1개
- 정치색 있는 소식 제외, 검증된 매체만, 과장 금지
- 원문 문장을 옮기지 않고 직접 요약, 출처 링크 필수
- 명언은 출처가 분명한 고전 위주
- 이미 앞선 호에서 다룬 소식은 다시 싣지 않는다

## 메일 구독
- 사이트 아래 구독 칸(동의 체크 필수) → `/api/subscribe` → 확인 메일 → 링크를 누르면 구독 완료(`/api/confirm`)
- `build.py`가 최신 호로 `newsletter/latest.json`(메일 원고)과 `newsletter/preview.html`(미리 보기)을 만든다
- `netlify/functions/newsletter-send.mjs`가 30분마다 돌며, 오늘(서울 기준) 호가 배포됐고 아직 안 보냈으면 확인된 구독자 전원에게 보낸다. 한 호는 한 번만 나간다
- 수신 거부: 메일 속 링크(`/api/unsubscribe`, 확인 버튼 한 번) 또는 메일 앱의 원클릭 수신 거부
- 구독자 명단은 Netlify Blobs(`subscribers` 저장소), 발송은 Resend
- Netlify 환경변수: `RESEND_API_KEY`(필수), `MAIL_FROM`(선택, 기본 `희소식 <news@heesosik.news>`), `NEWSLETTER_PAUSED=1`(발송 일시 중지)
