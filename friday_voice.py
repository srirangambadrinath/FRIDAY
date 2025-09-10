import threading
import queue
import os
from typing import Optional
import speech_recognition as sr

try:
	import pyttsx3
except Exception:  # optional alternative
	pyttsx3 = None


class FridayVoice:
	def __init__(self) -> None:
		self.recognizer = sr.Recognizer()
		self.microphone = sr.Microphone()
		self._init_tts()
		self._listen_lock = threading.Lock()
		self._audio_queue: "queue.Queue[bytes]" = queue.Queue()
		# Calibrate ambient noise
		try:
			with self.microphone as source:
				self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
		except Exception:
			pass

	def _init_tts(self) -> None:
		self.engine = None
		if pyttsx3 is not None:
			try:
				engine = pyttsx3.init()
				# Configure a slightly futuristic voice and rate if supported
				r = engine.getProperty("rate")
				engine.setProperty("rate", int(r * 0.95))
				# Prefer Indian English voice if available
				preferred_voice_id = os.getenv("FRIDAY_VOICE_ID", "").strip()
				voices = engine.getProperty("voices")
				selected_id = None
				if preferred_voice_id:
					selected_id = preferred_voice_id
				else:
					for v in voices:
						name_l = (getattr(v, "name", "") or "").lower()
						lang_l = ",".join(getattr(v, "languages", []) or []).lower()
						if "india" in name_l or "en-in" in lang_l or "hindi" in name_l:
							selected_id = v.id
							break
					# Fallback to any female/neutral English voice
					if not selected_id:
						for v in voices:
							name_l = (getattr(v, "name", "") or "").lower()
							if "female" in name_l or "zira" in name_l or "english" in name_l:
								selected_id = v.id
								break
				if selected_id:
					engine.setProperty("voice", selected_id)
				self.engine = engine
			except Exception:
				self.engine = None

	def say(self, text: str) -> None:
		if not text:
			return
		if self.engine is None:
			# Fallback to print if TTS not available
			print("FRIDAY:", text)
			return
		try:
			self.engine.stop()
			self.engine.say(text)
			self.engine.runAndWait()
		except Exception:
			print("FRIDAY:", text)

	def listen(self, timeout: float = 7.0, phrase_time_limit: float = 10.0) -> Optional[str]:
		with self._listen_lock:
			try:
				with self.microphone as source:
					audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
				txt = None
				try:
					lang = os.getenv("FRIDAY_ASR_LANG", "en-IN")
					txt = self.recognizer.recognize_google(audio, language=lang)
				except sr.UnknownValueError:
					self.say("Acoustics unclear. Could you repeat that, Boss?")
					return None
				except sr.RequestError:
					# offline recognize not configured; just ask again
					self.say("Network hiccup. Reattempting capture.")
					return None
				return txt
			except sr.WaitTimeoutError:
				return None
			except Exception as ex:
				print("Listen error:", ex)
				return None


