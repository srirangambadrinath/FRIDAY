import os
import sys
import time
import traceback
from typing import Optional

try:
	from dotenv import load_dotenv
except Exception:
	load_dotenv = None

from friday_voice import FridayVoice
from friday_brain import FridayBrain
from friday_system import FridaySystem
from friday_web import FridayWeb
from friday_status import report_status


def safe_load_env() -> None:
	if load_dotenv is not None:
		try:
			load_dotenv()
		except Exception:
			pass


def print_banner() -> None:
	banner = (
		"\n==============================\n"
		" FRIDAY AI Assistant \n"
		"==============================\n"
	)
	print(banner)


def main() -> None:
	safe_load_env()
	print_banner()

	voice = FridayVoice()
	brain = FridayBrain()
	system = FridaySystem(voice)
	web = FridayWeb()

	voice.say("Boot sequence complete. Systems online. Namaste Badri, Good to see you.")

	# Optional startup sound on Windows
	try:
		if sys.platform.startswith("win"):
			import winsound
			winsound.MessageBeep(winsound.MB_ICONASTERISK)
	except Exception:
		pass

	# Wake word configuration (optional)
	wake_word = os.getenv("FRIDAY_WAKE_WORD", "friday")
	continuous_mode = os.getenv("FRIDAY_CONTINUOUS", "true").lower() == "true"

	voice.say("Awaiting your command. Say 'Friday' to activate, or speak directly in continuous mode.")

	while True:
		try:
			query: Optional[str] = voice.listen()
			if not query:
				continue

			q_lower = query.lower().strip()

			if not continuous_mode and wake_word not in q_lower:
				# Ignore non wake-word utterances
				continue

			# Remove wake word prefix if present
			if q_lower.startswith(wake_word):
				query = query[len(wake_word):].strip(",. !?")

			# System-level shortcuts
			if any(k in q_lower for k in ("exit", "quit", "friday shutdown ")):
				voice.say("Powering down FRIDAY interface. Ping me when you need me, Boss.")
				break

			# Status report command (only on explicit request)
			if "status report" in q_lower or q_lower.strip() == "status":
				try:
					report_status(voice)
				except Exception:
					voice.say("Unable to compile the status report, Boss.")
				continue

			# Route intent: system, web, or brain
			handled = False

			try:
				handled = system.try_handle(query)
			except Exception as ex:
				voice.say("System control experienced turbulence. Containing the breach and moving on.")
				print("System control error:", ex)
				traceback.print_exc()

			if not handled:
				try:
					web_response = web.try_answer(query)
					if web_response:
						voice.say(web_response)
						handled = True
					else:
						# General Q&A: try Wikipedia → DuckDuckGo
						qa = web.fetch_answer(query)
						if qa and qa != "Sorry, I couldn't find an answer.":
							voice.say(qa)
							handled = True
				except Exception as ex:
					voice.say("Web subsystem had a hiccup. I will compensate with onboard cognition.")
					print("Web error:", ex)
					traceback.print_exc()

			if not handled:
				try:
					answer = brain.answer(query)
					voice.say(answer)
				except Exception as ex:
					voice.say("Cognitive array momentarily disrupted. Attempting graceful recovery.")
					print("Brain error:", ex)
					traceback.print_exc()

			# Small cooldown to prevent hot loop
			time.sleep(0.2)

		except KeyboardInterrupt:
			voice.say("Manual interrupt detected. Standing down with elegance.")
			break
		except Exception as loop_ex:
			print("Main loop error:", loop_ex)
			traceback.print_exc()
			# Attempt soft recovery rather than crash
			try:
				voice.say("Minor anomaly detected. Stabilizing and resuming operations.")
			except Exception:
				pass
			time.sleep(0.5)


if __name__ == "__main__":
	main()


