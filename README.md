# Morning Weather Bot

Open-Meteo API, Google Calendar iCal, Telegram Bot API를 사용해 매일 아침 날씨와 오늘 일정을 텔레그램으로 보내는 서버리스 알림 봇입니다.

서버를 계속 켜둘 필요 없이 GitHub Actions cron으로 정해진 시간에 실행됩니다. 기본 구성은 오늘 일정, 원주와 서울의 현재 날씨, 오늘 시간별 날씨, 내일 오전/오후 요약을 전송합니다.

## Features

- 여러 지역 현재 날씨 조회
- Google Calendar iCal 기반 오늘 일정 조회
- 오늘 날씨 3시간 단위 요약
- 내일 날씨 오전/오후 요약
- 텔레그램 모바일에서 읽기 쉬운 줄바꿈 포맷
- GitHub Actions 수동 실행 및 자동 실행 지원
- Open-Meteo API Key 불필요

## Message Format

```text
🌤 오늘의 날씨봇 (05/27 08:00)

[오늘 할일]
- 09:00 · 프론트 작업
- 14:00 · 주간회의

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
- Google Calendar iCal
- Telegram Bot API
- GitHub Actions

## Project Structure

```text
.
├─ weather_bot.py
├─ requirements.txt
├─ .env.example
└─ .github/
   └─ workflows/
      └─ weather.yml
```

## Local Setup

Create `.env` in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
WEATHER_BOT_TITLE=오늘의 날씨봇
GOOGLE_CALENDAR_ICAL_URL=your_google_calendar_private_ical_url
```

Install dependencies and run:

```powershell
pip install -r requirements.txt
python weather_bot.py
```

The script will:

1. Fetch weather forecast data from Open-Meteo.
2. Fetch today's events from Google Calendar iCal.
3. Normalize current, hourly, and tomorrow forecast values.
4. Format a Telegram-friendly message.
5. Send it through Telegram Bot API.

## GitHub Actions

Add these repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `WEATHER_BOT_TITLE` optional, if you want a custom title
- `GOOGLE_CALENDAR_ICAL_URL` optional, if you want today's calendar events

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
- Telegram bot tokens must be stored in GitHub Secrets, not in source code.
- Google Calendar private iCal URLs can expose calendar data if leaked. Store them only in `.env` or GitHub Secrets.
