# Morning Weather Bot

원주와 서울의 날씨를 매일 아침 텔레그램으로 보내는 개인용 자동화 봇입니다.

Open-Meteo API로 날씨 데이터를 가져오고, Telegram Bot API로 메시지를 전송합니다. 서버를 계속 켜둘 필요 없이 GitHub Actions cron으로 매일 한국시간 오전 8시에 실행됩니다.

## Features

- 원주, 서울 현재 날씨 조회
- 오늘 날씨 3시간 단위 요약
- 내일 날씨 오전/오후 요약
- 텔레그램 모바일에서 읽기 쉬운 줄바꿈 포맷
- GitHub Actions 수동 실행 및 자동 실행 지원

## Message Format

```text
🌤 우현님을 위한 날씨봇 (05/27 08:00)

[지금]
원주 18° · 체감 18° · 흐림
서울 20° · 체감 21° · 구름 조금

[오늘 시간별]
09시
- 원주 19° · 흐림 · 비 20%
- 서울 21° · 구름 조금 · 비 10%

[내일]
오전
- 원주 14~21° · 맑음 · 비 10% · 0mm
- 서울 16~23° · 맑음 · 비 10% · 0mm
```

## Tech Stack

- Python
- Open-Meteo API
- Telegram Bot API
- GitHub Actions

## Local Setup

Create `.env` in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Install dependencies and run:

```powershell
pip install -r requirements.txt
python weather_bot.py
```

## GitHub Actions

Add these repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The workflow runs every day at 08:00 KST:

```yaml
schedule:
  - cron: "0 23 * * *"
```

Manual test is available from:

```text
Actions -> weather -> Run workflow
```

## Notes

- `.env` is ignored by Git and must not be committed.
- Open-Meteo does not require an API key for this use case.
