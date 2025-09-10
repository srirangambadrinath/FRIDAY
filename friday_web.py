import os
import datetime as dt
from typing import Optional, List, Tuple

import requests
import feedparser
import wikipedia


class FridayWeb:
	def __init__(self) -> None:
		self.weather_api_key = os.getenv("OPENWEATHER_API_KEY")
		self.news_api_key = os.getenv("NEWSAPI_KEY") or os.getenv("NEWS_API_KEY")
		self.default_city = (os.getenv("FRIDAY_DEFAULT_CITY") or "Visakhapatnam").strip()

	def try_answer(self, query: str) -> Optional[str]:
		q = query.lower()
		if "time" in q:
			return self._get_time()
		if "weather" in q:
			city = self._extract_city(query) or self.default_city
			return self._get_weather(city)
		if "news" in q or "headlines" in q:
			loc = None
			if "visakhapatnam" in q or "vizag" in q or "local" in q:
				loc = "local"
			return self._get_news(locality=loc)
		return None

	def _get_time(self) -> str:
		now = dt.datetime.now().strftime("%A, %I:%M %p")
		return f"Local time check: {now}. Right on schedule, Boss."

	def _extract_city(self, query: str) -> Optional[str]:
		parts = query.split("in ")
		if len(parts) > 1:
			city = parts[1].strip().rstrip("?.! ")
			return city
		return None

	def _get_weather(self, city: Optional[str]) -> str:
		try:
			# Prefer OpenWeatherMap if key is set, else wttr.in fallback
			if self.weather_api_key and city:
				resp = requests.get(
					"https://api.openweathermap.org/data/2.5/weather",
					params={"q": city, "appid": self.weather_api_key, "units": "metric"},
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
			resp = requests.get(url, timeout=8)
			resp.raise_for_status()
			brief = resp.text.strip()
			if not brief:
				return "Weather data is shy at the moment. I will retry shortly."
			return f"{brief}. Forecast synced—adjusting mission parameters accordingly."
		except Exception:
			return "Weather uplink encountered interference. I'll try again soon."

	def _rss_feeds(self, locality: Optional[str]) -> List[str]:
		if locality == "local":
			return [
				"https://timesofindia.indiatimes.com/rssfeeds/-2128839596.cms",  # Hyderabad/Andhra feed (closest regional)
				"https://www.thehindu.com/news/cities/Visakhapatnam/feeder/default.rss",
				"https://www.newindianexpress.com/Cities/Visakhapatnam/rssfeed/?id=341&getXmlFeed=true",
			]
		# National India feeds
		return [
			"http://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
			"https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
			"https://www.thehindu.com/news/national/feeder/default.rss",
			"https://indianexpress.com/section/india/feed/",
		]

	def _get_news(self, locality: Optional[str] = None) -> str:
		feeds: List[str] = [
			* self._rss_feeds(locality)
		]
		try:
			entries = []
			for url in feeds:
				parsed = feedparser.parse(url)
				for e in parsed.entries[:10]:
					title = getattr(e, "title", "").strip()
					if title:
						entries.append({
							"title": title,
							"published": getattr(e, "published_parsed", None),
						})
			# Deduplicate by title while preserving order
			seen = set()
			unique = []
			for item in entries:
				t = item["title"]
				if t not in seen:
					seen.add(t)
					unique.append(item)
			# Sort by published if available (newest first)
			unique.sort(key=lambda x: (x["published"] is not None, x["published"]), reverse=True)
			top = [i["title"] for i in unique[:10]]
			if not top:
				return "No fresh headlines detected. The air is unusually calm, Boss."
			joined = "; ".join(top)
			if locality == "local":
				return f"Local headlines (Visakhapatnam region): {joined}."
			return f"National headlines (India): {joined}."
		except Exception:
			return "News scanners encountered interference. I will re-sync the feeds shortly."
	
	def fetch_answer(self, query: str) -> str:
		# 1) Try Wikipedia summary (2–3 sentences)
		try:
			wikipedia.set_lang("en")
			hits = wikipedia.search(query, results=1)
			if hits:
				page_title = hits[0]
				summary = wikipedia.summary(page_title, sentences=3, auto_suggest=True, redirect=True)
				if summary:
					return summary.strip()
		except Exception:
			pass

		# 2) Fallback: DuckDuckGo Instant Answer
		try:
			resp = requests.get(
				"https://api.duckduckgo.com/",
				params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
				timeout=8,
			)
			resp.raise_for_status()
			data = resp.json()
			text = (data.get("AbstractText") or "").strip()
			if not text:
				for item in data.get("RelatedTopics", []) or []:
					if isinstance(item, dict) and item.get("Text"):
						text = item["Text"].strip()
						break
			if text:
				return text
		except Exception:
			pass

		return "Sorry, I couldn't find an answer."

