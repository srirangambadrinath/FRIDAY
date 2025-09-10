import threading
import queue
import os
import tempfile
from typing import Optional
import speech_recognition as sr

try:
	import pyttsx3
except Exception:  # optional alternative
	pyttsx3 = None

try:
	from gtts import gTTS  # type: ignore
except Exception:
	gTTS = None  # type: ignore

try:
	from playsound import playsound  # type: ignore
except Exception:
	playsound = None  # type: ignore


class FridayVoice:
	def __init__(self) -> None:
		self.recognizer = sr.Recognizer()
		self._configure_recognizer()
		self.microphone = sr.Microphone()
		self._init_tts()
		self._listen_lock = threading.Lock()
		self._audio_queue: "queue.Queue[bytes]" = queue.Queue()
		# Calibrate ambient noise
		try:
			with self.microphone as source:
				self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
		except Exception:
			pass

	def _configure_recognizer(self) -> None:
		# Stronger noise handling and sensitivity tuning
		try:
			self.recognizer.energy_threshold = int(os.getenv("FRIDAY_ASR_ENERGY", "250"))
			self.recognizer.dynamic_energy_threshold = True
			self.recognizer.dynamic_energy_adjustment_damping = 0.15
			self.recognizer.dynamic_energy_ratio = 2.0
			self.recognizer.pause_threshold = float(os.getenv("FRIDAY_ASR_PAUSE", "0.6"))
			self.recognizer.phrase_threshold = float(os.getenv("FRIDAY_ASR_PHRASE", "0.2"))
			self.recognizer.non_speaking_duration = float(os.getenv("FRIDAY_ASR_NON_SPEAK", "0.3"))
		except Exception:
			pass

	def _init_tts(self) -> None:
		self.engine = None
		self.tts_provider = (os.getenv("FRIDAY_TTS_PROVIDER", "auto") or "auto").lower()
		self.azure_key = os.getenv("AZURE_TTS_KEY")
		self.azure_region = os.getenv("AZURE_TTS_REGION")
		self.eleven_key = os.getenv("ELEVENLABS_API_KEY")
		if pyttsx3 is not None:
			try:
				engine = pyttsx3.init()
				# Configure a slightly futuristic voice and faster rate if supported
				r = engine.getProperty("rate")
				# Target faster yet clear speech; allow override via env
				target_rate = int(os.getenv("FRIDAY_TTS_RATE", "200"))
				try:
					engine.setProperty("rate", target_rate)
				except Exception:
					engine.setProperty("rate", int(r * 1.2))
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
						if "india" in name_l or "en-in" in lang_l or "hindi" in name_l or "female" in name_l or "zira" in name_l:
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
		# Choose provider: Azure/ElevenLabs/gTTS/pyttsx3 in that order if configured
		provider = self._select_tts_provider()
		if provider == "azure":
			if self._say_azure(text):
				return
		elif provider == "elevenlabs":
			if self._say_elevenlabs(text):
				return
		elif provider == "gtts":
			if self._say_gtts(text):
				return
		# Fallback to pyttsx3 if available
		if self.engine is not None:
			try:
				self.engine.stop()
				self.engine.say(text)
				self.engine.runAndWait()
			except Exception:
				print("FRIDAY:", text)
				return
		else:
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
					self.say("Pardon me, Boss, could you repeat that?")
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

	def _select_tts_provider(self) -> str:
		if self.tts_provider in ("azure", "elevenlabs", "gtts", "pyttsx3"):
			return self.tts_provider
		# auto-detect
		if self.azure_key and self.azure_region:
			return "azure"
		if self.eleven_key:
			return "elevenlabs"
		if gTTS is not None and playsound is not None:
			return "gtts"
		return "pyttsx3"

	def _say_gtts(self, text: str) -> bool:
		if gTTS is None or playsound is None:
			return False
		try:
			lang = os.getenv("FRIDAY_TTS_LANG", "en")
			# Cache to a temporary MP3 and play
			with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
				mp3_path = tmp.name
			try:
				gTTS(text=text, lang=lang, slow=False).save(mp3_path)
				# Optional speed-up using pydub if available
				sped = os.getenv("FRIDAY_TTS_SPEED", "fast").lower() in ("fast", "faster", "1.2x")
				if sped:
					try:
						from pydub import AudioSegment  # type: ignore
						from pydub.effects import speedup  # type: ignore
						seg = AudioSegment.from_file(mp3_path, format="mp3")
						seg_fast = speedup(seg, playback_speed=float(os.getenv("FRIDAY_TTS_PLAYBACK", "1.2")))
						with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as sped_tmp:
							sped_path = sped_tmp.name
						seg_fast.export(sped_path, format="mp3")
						playsound(sped_path)
						try:
							os.unlink(sped_path)
						except Exception:
							pass
						return True
					except Exception:
						# Fallback to normal playback
						playsound(mp3_path)
						return True
				else:
					playsound(mp3_path)
					return True
			finally:
				try:
					os.unlink(mp3_path)
				except Exception:
					pass
		except Exception:
			return False

	def _say_azure(self, text: str) -> bool:
		# Optional Azure TTS placeholder; implement if SDK present
		try:
			from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig  # type: ignore
		except Exception:
			return False
		try:
			if not (self.azure_key and self.azure_region):
				return False
			speech_config = SpeechConfig(subscription=self.azure_key, region=self.azure_region)
			voice_name = os.getenv("AZURE_TTS_VOICE", "en-IN-NeerjaNeural")
			speech_config.speech_synthesis_voice_name = voice_name
			synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=AudioConfig(use_default_speaker=True))
			synthesizer.speak_text_async(text).get()
			return True
		except Exception:
			return False

	def _say_elevenlabs(self, text: str) -> bool:
		# Optional ElevenLabs TTS via REST API
		try:
			import requests  # type: ignore
		except Exception:
			return False
		try:
			if not self.eleven_key:
				return False
			voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # default Rachel
			resp = requests.post(
				f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
				headers={
					"xi-api-key": self.eleven_key,
					"accept": "audio/mpeg",
					"content-type": "application/json",
				},
				json={"text": text, "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1"), "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}},
				timeout=20,
			)
			if resp.status_code != 200:
				return False
			with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
				mp3_path = tmp.name
			try:
				for chunk in resp.iter_content(chunk_size=16384):
					if chunk:
						tmp.write(chunk)
				tmp.flush()
				if playsound is not None:
					playsound(mp3_path)
					return True
				return False
			finally:
				try:
					os.unlink(mp3_path)
				except Exception:
					pass
		except Exception:
			return False


