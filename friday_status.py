import os
import datetime as dt
from typing import Optional, Tuple

import requests
import feedparser

try:
	from friday_voice import FridayVoice
except Exception:
	FridayVoice = None  # type: ignore

try:
	from friday_web import FridayWeb
except Exception:
	FridayWeb = None  # type: ignore


def _get_time_phrase() -> Tuple[str, str]:
	now = dt.datetime.now()
	day = now.strftime("%A")
	time_24 = now.strftime("%H:%M")
	date_fmt = now.strftime("%d %B %Y")
	return time_24, f"{day}, {date_fmt}"


def _get_default_city() -> str:
	city = os.getenv("FRIDAY_DEFAULT_CITY") or os.getenv("CITY") or os.getenv("LOCATION")
	city = (city or "Visakhapatnam").strip()
	return city or "Visakhapatnam"


def _get_weather(city: Optional[str]) -> str:
	# Prefer OpenWeatherMap if API key provided; otherwise fallback to wttr.in
	try:
		api_key = os.getenv("OPENWEATHER_API_KEY")
		if api_key and city:
			resp = requests.get(
				"https://api.openweathermap.org/data/2.5/weather",
				params={"q": city, "appid": api_key, "units": "metric"},
				timeout=8,
			)
			resp.raise_for_status()
			data = resp.json()
			temp = data.get("main", {}).get("temp")
			desc = (data.get("weather") or [{}])[0].get("description", "").lower()
			name = data.get("name") or city
			if temp is not None and desc:
				return f"Weather in {name} is {int(round(float(temp)))}°C with {desc}."
		# Fallback: wttr.in concise text
		url = f"https://wttr.in/{city}?format=3" if city else "https://wttr.in/?format=3"
		wt = requests.get(url, timeout=8)
		wt.raise_for_status()
		brief = (wt.text or "").strip().rstrip('.')
		if brief:
			return brief + "."
		return "Unable to fetch weather data, Boss."
	except Exception:
		return "Unable to fetch weather data, Boss."


def _get_headlines() -> Tuple[str, str]:
	"""Return (local, national) headlines strings using FridayWeb sources if available."""
	try:
		if FridayWeb is not None:
			w = FridayWeb()
			local = w._get_news(locality="local")  # type: ignore[attr-defined]
			national = w._get_news(locality=None)  # type: ignore[attr-defined]
			return local, national
	except Exception:
		pass
	# Fallback minimal
	return "Local headlines are unavailable at the moment, Boss.", "National headlines are unavailable at the moment, Boss."


def _get_notifications_summary() -> str:
	# Placeholder notifications; wire up email/system integrations later
	try:
		unread_emails = int(os.getenv("FRIDAY_UNREAD_EMAILS", "2"))
		pending_alerts = int(os.getenv("FRIDAY_PENDING_ALERTS", "0"))
		total = unread_emails + pending_alerts
		if total == 0:
			return "No pending system notifications. All clear."
		parts = []
		if unread_emails:
			parts.append(f"{unread_emails} unread emails")
		if pending_alerts:
			parts.append(f"{pending_alerts} system alerts")
		return "You have " + " and ".join(parts) + "."
	except Exception:
		return "Notification systems are quiet or temporarily unavailable."


def status_report(voice: Optional["FridayVoice"] = None) -> str:
	"""
	Builds and speaks a concise, cinematic status report.
	If voice is None, will create a FridayVoice instance for speaking.
	Returns the plain-text report.
	"""
	local_voice = voice
	try:
		if local_voice is None and FridayVoice is not None:
			local_voice = FridayVoice()  # type: ignore[call-arg]
	except Exception:
		local_voice = None

	time_24, date_phrase = _get_time_phrase()
	city = _get_default_city()
	weather_text = _get_weather(city)
	local_headlines, national_headlines = _get_headlines()
	notifs = _get_notifications_summary()

	daypart = "morning"
	try:
		hour = int(time_24.split(":")[0])
		if 12 <= hour < 17:
			daypart = "afternoon"
		elif 17 <= hour < 22:
			daypart = "evening"
		elif hour >= 22 or hour < 5:
			daypart = "late hours"
	except Exception:
		pass

	# Speak greeting then immediately continue with the body—no pause
	greeting = f"Good {daypart}, Boss. The time is {time_24} hours on {date_phrase}."
	body = (
		f"{weather_text if weather_text else 'Weather systems are offline.'} "
		f"Local headline: {local_headlines} "
		f"National headline: {national_headlines} "
		f"{notifs} "
		f"Standing by for your next command."
	)

	try:
		if local_voice is not None:
			local_voice.say(greeting + " " + body)
	except Exception:
		pass

	return greeting + " " + body


# Backward/alias name for clarity in main.py
def report_status(voice: Optional["FridayVoice"] = None) -> str:
	return status_report(voice)


