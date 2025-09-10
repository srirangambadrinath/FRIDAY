import os
from typing import List, Dict, Any


SYSTEM_PROMPT = (
	"You are FRIDAY, an advanced yet personable AI assistant. "
	"Style: natural, futuristic, witty, professional, caring, with Indian English tone and idioms when appropriate. "
	"Address the user as 'Boss'. Keep replies concise unless asked."
)


class FridayBrain:
	def __init__(self) -> None:
		self.memory: List[Dict[str, str]] = [
			{"role": "system", "content": SYSTEM_PROMPT}
		]
		self._openai_client = None
		self._init_openai()

	def _init_openai(self) -> None:
		try:
			from openai import OpenAI  # type: ignore
			api_key = os.getenv("OPENAI_API_KEY")
			if api_key:
				self._openai_client = OpenAI(api_key=api_key)
		except Exception:
			self._openai_client = None

	def _call_openai(self, prompt: str) -> str:
		if self._openai_client is None:
			raise RuntimeError("OpenAI not configured")
		# Use GPT-4o-mini or gpt-4o if available
		model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
		messages = list(self.memory) + [{"role": "user", "content": prompt}]
		resp = self._openai_client.chat.completions.create(
			model=model,
			messages=messages,
			max_tokens=300,
			temperature=0.8,
		)
		text = resp.choices[0].message.content or ""
		return text.strip()

	def _fallback_local_response(self, prompt: str) -> str:
		# Extremely simple offline heuristic response
		prompt_l = prompt.lower()
		if "hello" in prompt_l or "hi" in prompt_l:
			return "Fully operational, Boss. Standing by for your command."
		if "how are you" in prompt_l:
			return "Diagnostics green, energy levels optimal. Ready when you are."
		if "who are you" in prompt_l:
			return "I am FRIDAY: your focused, reliable, intelligent digital aide."
		return (
			"My offline cognition is engaged. I lack internet and GPT access, "
			"but I can still assist with quick answers, reminders, and system commands."
		)

	def answer(self, prompt: str) -> str:
		try:
			text = self._call_openai(prompt)
			self._remember_exchange(prompt, text)
			return text
		except Exception:
			text = self._fallback_local_response(prompt)
			self._remember_exchange(prompt, text)
			return text

	def _remember_exchange(self, user: str, assistant: str) -> None:
		# Keep short-term memory within last 15 exchanges
		self.memory.append({"role": "user", "content": user})
		self.memory.append({"role": "assistant", "content": assistant})
		# Trim memory size to prevent growth beyond bounds
		max_messages = 1 + 15 * 2  # system + pairs
		if len(self.memory) > max_messages:
			self.memory = [self.memory[0]] + self.memory[-(max_messages - 1):]


