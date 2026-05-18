# Kulsh AI Bot 🍷🗿

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-AGPL_v3-green.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2)](https://discord.com/oauth2/authorize?client_id=1489421179461701663)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4)](https://t.me/Kulsh_aibot)

**Kulsh** is a foul-mouthed, witty, and oddly brilliant AI companion built for Discord and Telegram.  
He codes, cracks jokes, insults your friends (lovingly), and can join voice channels to listen and speak his mind.  
Powered by Google's Gemini API and a generous dose of post-Soviet humor.  
Now also a brutally honest **looksmaxxing analyst** – upload a face photo and get a full PSL rating, tier, and stylish infographic.

> *"Ты — Кульш, современная языковая модель ИИ... Используй сочетание «🍷🗿»..."*

---

## ✨ Features

- **Dual Platform** – Fully asynchronous operation across **Telegram** and **Discord** simultaneously.
- **Advanced Voice Interaction (Discord Exclusive)**  
  - **Speech Recognition:** Uses a custom `AudioSink` to listen to users. It has a **65% probability** to respond to any detected speech.
  - **Neural TTS:** High-fidelity voice synthesis via `edge-tts` (Microsoft Neural voices).
  - **Silence Detection:** Intelligent buffering that waits for a pause in speech before processing.
- **Contextual Memory** – Maintains a rolling context window (last 5 interactions) per chat to ensure coherent long-term conversations.
- **Vision Support** – Capable of analyzing images and providing sarcastic captions or technical descriptions.
- **AI Personality** – Custom-tuned system prompt for a unique "homie" persona that bypasses standard AI formalisms.
- **Remote Administration** – Built-in logging system that allows owners to retrieve `bot.log` files and live stdout directly via chat commands.
- **Automated Engagement** – Periodic auto-posting of "random thoughts" to keep the chat alive.
- **Donation System** – Support via Telegram Stars and DonationAlerts integration with a cross-platform leaderboard.
- **🔄 Auto-Update** – Authorized users can trigger a `git pull` and automatic restart directly from Discord (`кульш обновись`). Requires systemd setup.
- **🆕 Looksmaxxing Analysis** – Strict facial aesthetics evaluation.  
  Upload a photo (in Discord or Telegram) with the `кульш looksmaxxing` command and receive:
  - Objective **PSL rating** (1.0–8.0) and exact **tier** (Sub3 to True Adam / True Eve) with tier distribution chart
  - "You outperform X% of people" percentile based on normal distribution
  - Detailed breakdown of skin, eyes, jawline, bloat, bone structure, symmetry, canthal tilt
  - List of **strengths** and **weaknesses** (no sugarcoating)
  - Optional **improvement advice** (softmaxxing / hardmaxxing)
  - Stylish **infographic** with dark/light theme support and English/Russian language settings

---

## 🛠️ Tech Stack

- **Core:** Python 3.9+
- **AI Engine:** Google Generative AI (Gemini 2.5 Flash, Gemini 2.5 Flash Lite, Gemini Flash Latest, Gemini Flash Lite Latest, Gemini 3 Flash Preview, Gemini 3.1 Flash Lite Preview) — multiple models with automatic fallback
- **Frameworks:** `pyTelegramBotAPI` (Async), `discord.py` 2.x
- **Voice Processing:** `discord-ext-voice-receive`, `SpeechRecognition`, `pydub`
- **Audio/Networking:** `FFmpeg`, `aiohttp`, `edge-tts`
- **Image Processing:** `Pillow` (infographic generation for looksmaxxing reports)
- **Donations:** `python-socketio` (DonationAlerts listener)
- **Logging:** `RotatingFileHandler` for automated log management.

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/starfall-apk/kulsh.git
cd kulsh
```

### 2. Install Dependencies
Ensure you have **FFmpeg** installed on your host system (Linux: `sudo apt install ffmpeg`).
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
The bot requires a `.env` file to function. Create a file named `.env` in the root folder and populate it:
```env
# API Keys
TG_TOKEN=your_telegram_bot_token
DISCORD_TOKEN=your_discord_bot_token
AI_KEY=your_google_gemini_api_key_fallback
AI_KEY_1=your_primary_gemini_key
AI_KEY_2=your_secondary_gemini_key
AI_KEY_3=your_tertiary_gemini_key

# IDs & Configuration
TG_TARGET_CHAT=your_target_group_id
DS_ALLOWED_GUILD_ID=your_discord_server_id
DONATIONALERTS_CHANNEL_ID=your_donation_alerts_channel_id
DONATIONALERTS_TOKEN=your_donationalerts_token

# Optional
REPO_PATH=/path/to/bot/folder
```

**Note:** `AI_KEY` is a fallback. Use `AI_KEY_1`, `AI_KEY_2`, `AI_KEY_3` for the multi-model fallback system. The bot will cycle through all available model+key combinations on failure.

### 4. Launch
```bash
python kulsh.py
```

---

## 🖥️ Production Deployment (systemd + auto-update)

For the auto-update feature (`кульш обновись`), deploy the bot as a systemd service:

### 1. Configure Git in the bot directory
```bash
cd /path/to/bot/folder
git config --global user.email "bot@kulsh.ai"
git config --global user.name "Kulsh Bot"
git config --global pull.rebase false
```

### 2. Create systemd service
```bash
sudo nano /etc/systemd/system/kulsh.service
```

Paste (replace paths and user):
```ini
[Unit]
Description=Kulsh Discord Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/bot/folder
ExecStart=/usr/bin/python3 /path/to/bot/folder/kulsh.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. Enable and start
```bash
sudo systemctl daemon-reload
sudo systemctl enable kulsh
sudo systemctl start kulsh
```

### Useful management commands
```bash
sudo systemctl status kulsh       # Check status
sudo systemctl stop kulsh         # Stop bot
sudo systemctl start kulsh        # Start bot
sudo systemctl restart kulsh      # Manual restart
sudo journalctl -u kulsh -f       # Live logs
```

---

## 🎮 Commands

| Command | Platform | Description |
|---------|----------|-------------|
| `кульш [текст]` | Both | General interaction – chat, ask questions, get roasted. |
| `кульш настройки` | Both | View or change user settings (language, theme). |
| `кульш настройки язык ru/en` | Both | Set infographic language (Russian/English). |
| `кульш настройки тема dark/light` | Both | Set infographic theme (dark/light). |
| `кульш донаты` | Both | Show top donators leaderboard. |
| `кульш зайди в войс` | Discord | Summons the bot to your voice channel (starts listening with 65% response chance). |
| `кульш скажи в войсе [текст]` | Discord | Make the bot speak in voice using neural TTS. |
| `кульш выйди из войса` | Discord | Disconnects the bot from voice. |
| `кульш логи` | Discord | (Authorized only) Sends the current `bot.log` file to the chat. |
| `кульш обновись` | Discord | (Authorized only) Runs `git pull` and auto-restarts via systemd if updates found. |
| `кульш серия` | Discord | Sends a streak reminder to a designated user. |
| **🆕 `кульш looksmaxxing`** | Both | **Facial aesthetics analysis.**<br/>Send with an attached photo to get a full PSL breakdown and infographic.<br/>Add `совет` or `advice` in the caption for practical tips. |

---

## 📊 Looksmaxxing System

The bot evaluates faces using a strict, objective AI analyst persona. The PSL scale uses normal distribution to map facial aesthetics:

### Tier Distribution
| Tier | PSL Range | Percentile |
|------|-----------|------------|
| SUB 3 | 1.0 – 2.9 | ~2.3% |
| SUB 5 | 3.0 – 4.9 | ~13.6% |
| LTN / LTB | 5.0 – 5.5 | ~10.0% |
| MTN / MTB | 5.6 – 6.3 | ~19.2% |
| HTN / HTB | 6.4 – 7.0 | ~19.2% |
| CHADLITE / STACYLITE | 7.0 – 7.4 | ~13.6% |
| CHAD / STACY | 7.5 – 7.7 | ~10.0% |
| TRUE ADAM / TRUE EVE | 7.8 – 8.0 | ~2.3% |

### Analysis Includes
- Gender detection (Male/Female with appropriate tier naming)
- 8 facial metrics (skin, eyes, jawline, bloat, hair, bone structure, symmetry, canthal tilt)
- "You outperform X% of people" based on exact PSL positioning within the tier
- Tier distribution bar chart with highlighted current tier
- Visual infographic with profile photo, metrics table, pros/cons list
- Optional practical looksmaxxing advice (softmaxxing/hardmaxxing)

---

## 👥 Credits & Special Thanks

### Development Team
- **starfall-apk (st6rf9ll)** — Lead Author, Creator & AI Logic Architect (formerly *downfalls2920*).
- **pomidorka1515 (pomi)** — Co-author & Infrastructure (Bot Hosting & Linux Optimization).

### Special Thanks
- **"Секретный чат"** — The legendary Discord server where Kulsh was born, tested, and raised.
- **Kulsh** — My close friend whose name and personality inspired the creation of this bot.

---

## 📞 Contact & Support

If you have any technical questions, suggestions, or just want to chat about the project:

- **starfall-apk (Lead Dev):** [Telegram](https://t.me/wf9ll) | Discord: `st6rf9ll`
- **pomidorka1515 (Hosting):** [Telegram](https://t.me/pomidorka_1515) | Discord: `pomidorka1515`

Project Link: [https://github.com/starfall-apk/kulsh](https://github.com/starfall-apk/kulsh)

Web Version: [https://kulsh-ai.web.app/](https://kulsh-ai.web.app/)

Donate: [https://kulsh-ai.web.app/donate.html](https://kulsh-ai.web.app/donate.html)

---

## 📜 License
This project is licensed under the AGPL v3.0 License – see the [LICENSE file](LICENSE) for details.
