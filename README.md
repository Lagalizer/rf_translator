# RF Online Translator

Real-time two-way chat translator for **RF Online** (RF ONLINE NEXT). It reads the in-game chat, translates every message with an AI (local or cloud), shows it in a transparent overlay over the game and can read it aloud. You can also talk into your microphone: your speech is translated and typed into the game chat.

It only looks at the screen and types like a keyboard. It never reads game memory or network traffic.

## Features

- **Chat translation (OCR → AI → overlay)**: reads the game's chat panel directly from the game window (Tesseract OCR, English + Cyrillic). The overlay can be anywhere and any size.
- **Multi-language chat**: *Auto* detects the language of each line, so players can write in Russian, English, Portuguese, Spanish and more in the same chat.
- **Reads in order, never repeats**: when you open the chat or switch channel it translates and reads everything not read yet, in order. It never repeats messages, even after you close and reopen the chat or restart the app.
- **Channel tabs**: the overlay has the same channels as the game (All, World, Server, Party, Guild, Raid, Whisper…) and follows the game's active tab.
- **Name alert**: plays a sound you choose (repeat N times, every X s for Y s, plus optional spoken text) when someone writes your character name, even with OCR mistakes or in Cyrillic.
- **Neural voice (edge-tts)**: reads “*Name says: message*”, with adjustable speed and pitch. When many messages are waiting it reads a bit faster. Russian names are transliterated for non-Russian voices.
- **Voice → game chat**: hold, tap or continuous microphone modes, with beeps that tell you when to speak, and a **cancel key** (default Esc) that stops a dictation at once and erases what was typed. Voice commands: `reply …` answers the last PM, and `change to chat guild/server/party…` switches channel (works in 7 languages). Replies go out in the other player's language when the app knows it.
- **AI of your choice**:
  - **Local** with Ollama (free, private, offline). No model comes with the app: the ☁ AI Clouds guide has a table of local models by graphics memory (VRAM) and RAM, with the ones tested here. Only the model in use stays loaded (two if the voice uses another local model), and everything is unloaded when the app closes, even after a crash. The 📊 Ratings tab tests how fast a model runs on your PC.
  - **Cloud**: OpenAI, DeepSeek, Anthropic Claude, Google Gemini, xAI Grok, Mistral, Groq, Qwen, OpenRouter, NVIDIA, Together, Cerebras, Fireworks, Perplexity, Ollama Cloud, plus **two custom OpenAI-compatible servers** (URL + key + model).
  - Separate AI for the voice, automatic fallback to another AI when one fails, and searchable model lists (type `free`).
  - Two identical AI panels (chat and voice): key, model with search, 🆓 only-free filter (free = green, ⛔ = refused by your account), requests per minute, custom server names.
  - **Model profiles and options** for each AI (chat and voice): temperature, thinking on/off, context, answer length and lines per request, with tested defaults. Built-in ⭐ profiles, and you can save your own.
  - OpenRouter free tier support: “thinking” is turned off for fast answers (~1 s instead of ~9 s), untranslated lines are retried, and the free requests left today are shown.
- **Overlay**: drag, resize, lock with click-through (Ctrl+Shift+L), auto-hide after X seconds, background opacity, colors per speaker, light/dark theme. The overlay only shows while the game or the app is in front.
- **7 interface languages**: English, Português, Español, Français, Deutsch, Русский, Italiano, each with a built-in manual (📖 Manual button).
- **Private by design**: API keys are encrypted with Windows DPAPI. Game captures, OCR and the voice stay in memory only, so no screenshots or audio are ever written to disk.

## Installation (Windows 10/11)

You don't need to install Python: the app downloads its own Python into its `python\` folder, and everything stays inside the app folder.

1. Download this repository (**Code → Download ZIP**) and unzip it.
2. Run **`install.bat`**. It first asks your language (English, Português, Español, Français, Deutsch, Русский, Italiano): the installer, the app and its start-up messages use it (you can change it later in the app). Then it creates **`RF Translator.exe`** and prepares the app's own Python (only the first time, a few minutes). Accept the administrator prompt, because the game runs as administrator.
3. Open **`RF Translator.exe`**. The first start installs whatever is still missing (Tesseract OCR, language packs, Ollama for the local AI).
4. Follow the **📖 Manual** in the app. It opens automatically the first time. The **☁ AI Clouds** tab lists the free cloud AIs, their limits, whether they ask for a card, and which local model fits your PC.

Without the .exe: run `run.bat` (after `install.bat`). To rebuild the launcher, run `launcher\build.bat`.

## Quick start

1. Write your character name (your own messages are ignored).
2. Choose the chat AI: **Local** (download a model with 🤗; see ☁ AI Clouds for which one fits your PC) or **Cloud**. For the cloud, paste the key in the AI's panel and press **Test**. Free models are green; tick 🆓 *Only free* to never use a paid one.
3. Source language **Auto**, translate to your language.
4. Pick the microphone, the languages you speak and write in, and the voice hotkey (default F11).
5. Press **▶ Start translator** and open the game chat.

> **Free AIs:** all OpenRouter `:free` models share **50 requests per day** without credits (1000 per day after buying 10 credits). One request translates up to 6 chat lines (configurable).
> For a whole day for free, use the **local** AI (no limit), **Mistral**'s free plan (~1 request per second), **Google Gemini** Flash-Lite (~1000 per day), **Groq** (free models only: with a card on the account, the models with a price are billed) or **NVIDIA**, and set a second AI as the fallback. The ☁ AI Clouds guide says which ones ask for a card.

## Files

| File | What it is |
|---|---|
| `main.py` | Interface: settings window, overlay, manual, tray icon |
| `core.py` | Engine: game capture and OCR, chat reading, AI, voice, microphone, hotkeys |
| `bootstrap.py` | First-start setup (dependencies, Tesseract, Ollama) and cloud provider list |
| `i18n.py`, `manual.py`, `ai_clouds.py`, `ai_ratings.py` | Interface translations, the in-app manual, the AI Clouds guide and the AI ratings with the speed test (7 languages) |
| `launcher/` | Source of `RF Translator.exe` (starts the app as administrator, no console) |
