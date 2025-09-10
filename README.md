FRIDAY – Your Personal AI Assistant (Windows, Python 3.10+)

FRIDAY is a modular desktop voice assistant with a witty, futuristic personality. It listens, thinks (OpenAI GPT), controls apps, searches the web, and fetches time, weather, and news.

Features
- Voice I/O via `speech_recognition` and `pyttsx3`
- GPT intelligence with short-term memory; offline fallback
- System control: open Chrome/VS Code/Spotify; Google/YouTube/Wikipedia searches; volume/power controls
- Web info: local time, weather (OpenWeather), news (NewsAPI)
- Robust error handling; Windows-friendly

Installation
1. Install Python 3.10+ and ensure it’s on PATH.
2. Open PowerShell in the project folder.
3. Create and activate a virtual environment:
   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. (Optional) Copy `.env.example` to `.env` and set values:
   ```powershell
   copy .env.example .env
   ```

Run
```powershell
python main.py
```
You’ll hear a startup chime and FRIDAY will announce readiness.

Sample commands
- “Friday, open Chrome”
- “Google quantum computing”
- “What’s the weather in New York?”
- “How are you?”
- Say “exit” to terminate.

Troubleshooting
- Audio/mic: Check Windows privacy settings. First launch calibrates ambient noise (~0.6s).
- OpenAI errors: Ensure `OPENAI_API_KEY` is set and network is available.
- If TTS fails, FRIDAY prints responses to console.


