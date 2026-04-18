# Kulsh AI Bot 🍷🗿

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2)]([https://discord.com](https://discord.com/oauth2/authorize?client_id=1489421179461701663))
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4)](https://t.me/Kulsh_aibot)

**Kulsh** is a foul‑mouthed, witty, and oddly brilliant AI companion built for Discord and Telegram.  
He codes, cracks jokes, insults your friends (lovingly), and can join voice channels to listen and speak his mind.  
Powered by Google's Gemini API (Gemma-3-4b-it) and a generous dose of post‑Soviet humor.

> *"Ты — Кульш, современная языковая модель ИИ... Используй сочетание «🍷🗿»..."*

---

## ✨ Features

- **Dual Platform** – Fully asynchronous operation across **Telegram** and **Discord** simultaneously.
- **Advanced Voice Interaction (Discord Exclusive)** - **Speech Recognition:** Uses a custom `AudioSink` to listen to users. It has a **65% probability** to respond to any detected speech.
  - **Neural TTS:** High-fidelity voice synthesis via `edge-tts` (Microsoft Neural voices).
  - **Silence Detection:** Intelligent buffering that waits for a pause in speech before processing.
- **Contextual Memory** – Maintains a rolling context window (last 10 interactions) per chat to ensure coherent long-term conversations.
- **Vision Support** – Capable of analyzing images and providing sarcastic captions or technical descriptions.
- **AI Personality** – Custom-tuned system prompt for a unique "homie" persona that bypasses standard AI formalisms.
- **Remote Administration** – Built-in logging system that allows owners to retrieve `bot.log` files and live stdout directly via chat commands.
- **Automated Engagement** – Periodic auto-posting of "random thoughts" to keep the chat alive.

---

## 🛠️ Tech Stack

- **Core:** Python 3.9+
- **AI Engine:** Google Generative AI (Gemma 3 Flash)
- **Frameworks:** `pyTelegramBotAPI` (Async), `discord.py` 2.x
- **Voice Processing:** `discord-ext-voice-receive`, `SpeechRecognition`, `pydub`
- **Audio/Networking:** `FFmpeg`, `aiohttp`, `edge-tts`
- **Logging:** `RotatingFileHandler` for automated log management.

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone [https://github.com/starfall-apk/kulsh.git](https://github.com/starfall-apk/kulsh.git)
cd kulsh

```
### 2. Install Dependencies
Ensure you have **FFmpeg** installed on your host system (Linux: sudo apt install ffmpeg).
```bash
pip install -r requirements.txt

```
### 3. Environment Configuration
The bot requires a .env file to function. Create a file named .env in the root folder and populate it:
```env
# API Keys
TG_TOKEN=your_telegram_bot_token
DISCORD_TOKEN=your_discord_bot_token
AI_KEY=your_google_gemini_api_key

# IDs & Configuration
TG_TARGET_CHAT=your_target_group_id
DS_ALLOWED_GUILD_ID=your_discord_server_id
OWNER_IDS=12345678,87654321  # Comma-separated user IDs for log access

```
### 4. Launch
```bash
python kulsh.py

```
## 🎮 Commands
 * кульш [текст] — General interaction.
 * кульш зайди в войс — Summons the bot to your voice channel (starts listening).
 * кульш выйди — Disconnects the bot from voice.
 * кульш логи — (Authorized only) Sends the current bot.log file to the chat.
## 👥 Credits & Special Thanks
### Development Team
 * **starfall-apk (st6rf9ll)** — Lead Author, Creator & AI Logic Architect (formerly *downfalls2920*).
 * **pomidorka1515 (pomi)** — Co-author & Infrastructure (Bot Hosting & Linux Optimization).
### Special Thanks
 * **"Секретный чат"** — The legendary Discord server where Kulsh was born, tested, and raised.
 * **Kulsh** — My close friend whose name and personality inspired the creation of this bot.
## 📞 Contact & Support

If you have any technical questions, suggestions, or just want to chat about the project:

* **starfall-apk (Lead Dev):** [Telegram](https://t.me/wf9ll) | Discord: `st6rf9ll`
* **pomidorka1515 (Hosting):** [Telegram](https://t.me/pomidorka_1515) | Discord: `pomidorka1515`

Project Link: [https://github.com/starfall-apk/kulsh](https://github.com/starfall-apk/kulsh)
## 📜 License
This project is licensed under the MIT License - see the [LICENSE file](LICENSE) for details.
