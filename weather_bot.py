import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from icalendar import Calendar
from dotenv import load_dotenv


load_dotenv(encoding="utf-8-sig")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LOCATIONS = [
    {"name": "원주", "latitude": 37.3422, "longitude": 127.9202},
    {"name": "서울", "latitude": 37.5665, "longitude": 126.9780},
]

TIMEZONE = "Asia/Seoul"
MORNING_REPORT_TITLE = os.getenv("WEATHER_BOT_TITLE") or "우현님을 위한 아침 보고"
EVENING_REPORT_TITLE = os.getenv("EVENING_REPORT_TITLE") or "우현님을 위한 내일 보고"

WEATHER_LABELS = {
    0: "맑음",
    1: "대체로 맑음",
    2: "구름 조금",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    56: "어는 이슬비",
    57: "강한 어는 이슬비",
    61: "비",
    63: "비",
    65: "강한 비",
    66: "어는 비",
    67: "강한 어는 비",
    71: "눈",
    73: "눈",
    75: "강한 눈",
    77: "싸락눈",
    80: "소나기",
    81: "소나기",
    82: "강한 소나기",
    85: "눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "우박 동반 뇌우",
    99: "강한 우박 동반 뇌우",
}

# Higher score wins when choosing a representative weather code for a time block.
WEATHER_SEVERITY = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    45: 4,
    48: 4,
    51: 5,
    53: 5,
    55: 6,
    56: 6,
    57: 7,
    61: 8,
    63: 9,
    65: 10,
    66: 9,
    67: 10,
    71: 8,
    73: 9,
    75: 10,
    77: 8,
    80: 8,
    81: 9,
    82: 10,
    85: 9,
    86: 10,
    95: 11,
    96: 12,
    99: 13,
}


def request_json(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def request_bytes(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return response.read()


def build_open_meteo_url(location):
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,apparent_temperature,weather_code",
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code",
        "timezone": TIMEZONE,
        "forecast_days": 2,
    }
    return "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)


def fetch_weather(location):
    return request_json(build_open_meteo_url(location))


def round_temp(value):
    return round(float(value))


def format_mm(value):
    value = float(value)
    if value == 0:
        return "0mm"
    return f"{value:.1f}mm"


def weather_label(code):
    return WEATHER_LABELS.get(int(code), f"코드 {code}")


def choose_weather_code(codes):
    counts = Counter(int(code) for code in codes)
    return max(
        counts,
        key=lambda code: (WEATHER_SEVERITY.get(code, 0), counts[code]),
    )


def aggregate_period(hourly, target_date, start_hour, end_hour):
    items = []
    for index, time_text in enumerate(hourly["time"]):
        dt = datetime.fromisoformat(time_text)
        if dt.date() == target_date and start_hour <= dt.hour <= end_hour:
            items.append(index)

    if not items:
        raise ValueError(f"No hourly data for {target_date} {start_hour}-{end_hour}")

    temps = [hourly["temperature_2m"][i] for i in items]
    rain_probs = [hourly["precipitation_probability"][i] or 0 for i in items]
    rains = [hourly["precipitation"][i] or 0 for i in items]
    codes = [hourly["weather_code"][i] for i in items]

    return {
        "min_temp": round_temp(min(temps)),
        "max_temp": round_temp(max(temps)),
        "rain_probability": int(max(rain_probs)),
        "precipitation": sum(float(value) for value in rains),
        "weather": weather_label(choose_weather_code(codes)),
    }


def pick_hourly_points(hourly, target_date, hours):
    points = []
    for hour in hours:
        expected_time = f"{target_date.isoformat()}T{hour:02d}:00"
        try:
            index = hourly["time"].index(expected_time)
        except ValueError:
            continue

        points.append(
            {
                "hour": hour,
                "temperature": round_temp(hourly["temperature_2m"][index]),
                "rain_probability": int(hourly["precipitation_probability"][index] or 0),
                "weather": weather_label(hourly["weather_code"][index]),
            }
        )
    return points


def normalize_weather(location, payload):
    now = datetime.now(ZoneInfo(TIMEZONE))
    today = now.date()
    tomorrow = today + timedelta(days=1)
    current = payload["current"]

    return {
        "name": location["name"],
        "current": {
            "temperature": round_temp(current["temperature_2m"]),
            "apparent": round_temp(current["apparent_temperature"]),
            "weather": weather_label(current["weather_code"]),
        },
        "today_hourly": pick_hourly_points(payload["hourly"], today, [9, 12, 15, 18, 21]),
        "tomorrow_am": aggregate_period(payload["hourly"], tomorrow, 6, 11),
        "tomorrow_pm": aggregate_period(payload["hourly"], tomorrow, 12, 23),
    }


def format_period_line(location_weather, key):
    data = location_weather[key]
    return (
        f"{location_weather['name']} "
        f"{data['min_temp']}~{data['max_temp']}° · "
        f"{data['weather']} · "
        f"비 {data['rain_probability']}% · "
        f"{format_mm(data['precipitation'])}"
    )


def as_local_datetime(value, default_time):
    tz = ZoneInfo(TIMEZONE)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tz)
        return value.astimezone(tz)
    if isinstance(value, date):
        return datetime.combine(value, default_time, tzinfo=tz)
    raise TypeError(f"Unsupported calendar date type: {type(value)}")


def fetch_calendar():
    ical_url = os.getenv("GOOGLE_CALENDAR_ICAL_URL")
    if not ical_url:
        return None

    try:
        return Calendar.from_ical(request_bytes(ical_url))
    except (urllib.error.URLError, ValueError) as error:
        print(f"Calendar fetch skipped: {error}")
        return None


def extract_events_for_date(calendar, target_date):
    if calendar is None:
        return []

    tz = ZoneInfo(TIMEZONE)
    start_of_day = datetime.combine(target_date, time.min, tzinfo=tz)
    end_of_day = start_of_day + timedelta(days=1)
    events = []

    for component in calendar.walk("VEVENT"):
        summary = str(component.get("summary", "제목 없음")).strip()
        start_value = component.decoded("dtstart")
        end_value = component.decoded("dtend", start_value)
        start_dt = as_local_datetime(start_value, time.min)
        end_dt = as_local_datetime(end_value, time.max)

        if end_dt <= start_of_day or start_dt >= end_of_day:
            continue

        is_all_day = isinstance(start_value, date) and not isinstance(start_value, datetime)
        events.append(
            {
                "summary": summary,
                "start": start_dt,
                "all_day": is_all_day,
            }
        )

    return sorted(events, key=lambda event: (event["start"], event["summary"]))


def format_events_section(title, events):
    lines = [f"[{title}]"]
    if not events:
        lines.append("등록된 일정 없음")
        return lines

    for event in events[:8]:
        if event["all_day"]:
            lines.append(f"- 종일 · {event['summary']}")
        else:
            lines.append(f"- {event['start'].strftime('%H:%M')} · {event['summary']}")

    if len(events) > 8:
        lines.append(f"- 외 {len(events) - 8}개 일정")
    return lines


def report_mode(now_dt):
    mode = (os.getenv("REPORT_MODE") or "").strip().lower()
    if mode in {"morning", "evening"}:
        return mode
    return "evening" if now_dt.hour >= 18 else "morning"


def append_today_weather(lines, weather_by_location):
    lines.append("[지금]")
    for weather in weather_by_location:
        current = weather["current"]
        lines.append(
            f"{weather['name']} "
            f"{current['temperature']}° · "
            f"체감 {current['apparent']}° · "
            f"{current['weather']}"
        )

    lines.append("")
    lines.append("[오늘 시간별]")
    hours = sorted(
        {
            point["hour"]
            for weather in weather_by_location
            for point in weather["today_hourly"]
        }
    )
    for hour in hours:
        lines.append(f"{hour:02d}시")
        for weather in weather_by_location:
            point = next(
                item for item in weather["today_hourly"] if item["hour"] == hour
            )
            lines.append(
                f"- {weather['name']} {point['temperature']}° · "
                f"{point['weather']} · 비 {point['rain_probability']}%"
            )


def append_tomorrow_weather(lines, weather_by_location):
    lines.append("[내일 날씨]")
    for title, key in [("오전", "tomorrow_am"), ("오후", "tomorrow_pm")]:
        lines.append(title)
        for weather in weather_by_location:
            data = weather[key]
            lines.append(
                f"- {weather['name']} {data['min_temp']}~{data['max_temp']}° · "
                f"{data['weather']} · 비 {data['rain_probability']}% · "
                f"{format_mm(data['precipitation'])}"
            )


def format_message(weather_by_location):
    now_dt = datetime.now(ZoneInfo(TIMEZONE))
    now = now_dt.strftime("%m/%d %H:%M")
    mode = report_mode(now_dt)
    calendar = fetch_calendar()
    today_events = extract_events_for_date(calendar, now_dt.date())
    tomorrow_events = extract_events_for_date(
        calendar, now_dt.date() + timedelta(days=1)
    )

    if mode == "evening":
        lines = [
            f"🌙 {EVENING_REPORT_TITLE} ({now})",
            "",
            *format_events_section("내일 할일", tomorrow_events),
            "",
        ]
        append_tomorrow_weather(lines, weather_by_location)
    else:
        lines = [
            f"🌤 {MORNING_REPORT_TITLE} ({now})",
            "",
            *format_events_section("오늘 할일", today_events),
            "",
        ]
        append_today_weather(lines, weather_by_location)

    return "\n".join(lines)


def send_telegram(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request_json(request)


def main():
    weather_by_location = []
    for location in LOCATIONS:
        payload = fetch_weather(location)
        weather_by_location.append(normalize_weather(location, payload))

    message = format_message(weather_by_location)
    print(message)
    send_telegram(message)


if __name__ == "__main__":
    main()
