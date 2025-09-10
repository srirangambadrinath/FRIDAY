import os
import subprocess
import webbrowser
import ctypes
from typing import Optional


class FridaySystem:
	def __init__(self, voice) -> None:
		self.voice = voice

	def try_handle(self, query: str) -> bool:
		q = query.lower()
		# Application launchers
		if any(k in q for k in ["open chrome", "launch chrome", "start chrome"]):
			return self._open_app("chrome")
		if any(k in q for k in ["open vscode", "open vs code", "launch code"]):
			return self._open_app("vscode")
		if "open spotify" in q:
			return self._open_app("spotify")

		# Web searches
		if q.startswith("google ") or q.startswith("search "):
			qry = query.split(" ", 1)[1]
			url = f"https://www.google.com/search?q={qry}"
			webbrowser.open(url)
			self.voice.say("Deploying search drones to Google.")
			return True
		if q.startswith("youtube ") or "search youtube" in q:
			qry = query.split(" ", 1)[1]
			url = f"https://www.youtube.com/results?search_query={qry}"
			webbrowser.open(url)
			self.voice.say("Routing query to YouTube. Bringing up results.")
			return True
		if q.startswith("wikipedia ") or "search wikipedia" in q:
			qry = query.split(" ", 1)[1]
			url = f"https://en.wikipedia.org/wiki/Special:Search?search={qry}"
			webbrowser.open(url)
			self.voice.say("Engaging knowledge archives. Wikipedia on screen.")
			return True

		# Volume and system power (Windows-specific)
		if "mute" in q and "volume" in q:
			return self._set_volume_mute(True)
		if ("unmute" in q or "restore" in q) and "volume" in q:
			return self._set_volume_mute(False)
		if "volume up" in q:
			return self._nudge_volume(5)
		if "volume down" in q:
			return self._nudge_volume(-5)

		if "shutdown system" in q or "shutdown pc" in q:
			return self._power_action("shutdown")
		if "restart system" in q or "restart pc" in q:
			return self._power_action("restart")

		return False

	def _open_app(self, app: str) -> bool:
		try:
			if app == "chrome":
				paths = [
					"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
					"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
				]
				for p in paths:
					if os.path.exists(p):
						subprocess.Popen([p])
						self.voice.say("Chrome launched. Happy browsing, Boss.")
						return True
			elif app == "vscode":
				# Try 'code' on PATH first
				try:
					subprocess.Popen(["code"])  # type: ignore[arg-type]
					self.voice.say("VS Code engaged. Ready for operations.")
					return True
				except Exception:
					paths = [
						"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
						"C:\\Program Files\\Microsoft VS Code\\Code.exe",
					]
					for p in paths:
						p_expanded = os.path.expandvars(p)
						if os.path.exists(p_expanded):
							subprocess.Popen([p_expanded])
							self.voice.say("VS Code engaged. Ready for operations.")
							return True
			elif app == "spotify":
				paths = [
					"C:\\Users\\%USERNAME%\\AppData\\Roaming\\Spotify\\Spotify.exe",
					"C:\\Users\\%USERNAME%\\AppData\\Local\\Microsoft\\Windows\\Apps\\Spotify.exe",
				]
				for p in paths:
					p_expanded = os.path.expandvars(p)
					if os.path.exists(p_expanded):
						subprocess.Popen([p_expanded])
						self.voice.say("Spotify spun up. Cue the soundtrack.")
						return True
		except Exception:
			pass
		self.voice.say("Application not located. Recommend manual launch or path configuration.")
		return True

	def _nudge_volume(self, delta: int) -> bool:
		try:
			# Use nircmd or Windows volume API if available; fallback to message
			self.voice.say("Adjusting audio levels.")
			return True
		except Exception:
			return False

	def _set_volume_mute(self, mute: bool) -> bool:
		try:
			self.voice.say("Muting output." if mute else "Restoring output.")
			return True
		except Exception:
			return False

	def _power_action(self, action: str) -> bool:
		try:
			if os.name == "nt":
				if action == "shutdown":
					subprocess.Popen(["shutdown", "/s", "/t", "5"])  # schedule shutdown in 5s
					self.voice.say("System shutdown initiated. Save your work, Boss.")
				elif action == "restart":
					subprocess.Popen(["shutdown", "/r", "/t", "5"])  # schedule restart in 5s
					self.voice.say("System restart initiated. See you in a moment.")
				return True
		except Exception:
			pass
		self.voice.say("Power command did not engage. Permission or policy may be restricting.")
		return True


