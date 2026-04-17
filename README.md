# Kulsh AI Bot 🍷🗿

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2)](https://discord.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4)](https://telegram.org)

**Kulsh** is a foul‑mouthed, witty, and oddly brilliant AI companion built for Discord and Telegram.  
He codes, cracks jokes, insults your friends (lovingly), and can even join voice channels to speak his mind.  
Powered by Google's Gemini API and a generous dose of post‑Soviet humor.

> *"Ты — Кульш, современная ядыковая модель ИИ... Твои кенты: Антон (Рекми), Богдан (Фолз), Фёдор (Понил)..."*

---

## ✨ Features

- **Dual Platform** – Works simultaneously in **Telegram** groups and **Discord** servers.
- **Contextual Memory** – Remembers the last 5 interactions *per chat/channel*.
- **AI Personality** – Speaks like a sarcastic Russian dude from your homies' chat.
- **Image Generation (Random)** – Sends a random themed image with a custom AI‑generated caption when asked for a "photo".
- **Discord Voice Integration**  
  - `кульш зайди в войс <channel_id>` – Joins your voice channel.  
  - `кульш скажи в войсе <text>` – Speaks the text aloud using neural TTS.  
  - `кульш выйди из войса` – Leaves the channel.
- **Auto‑Posting** – Every 1–4 hours, Kulsh drops a random thought or meme into the configured Telegram chat.
- **Fully Async** – Built with `asyncio`, `aiohttp`, and `discord.py` 2.x for smooth performance.

---

## 🛠️ Tech Stack

- **Python 3.9+**
- `aiogram` / `pyTelegramBotAPI` (async) – Telegram interface
- `discord.py` – Discord interface
- `aiohttp` – Async HTTP requests
- `edge-tts` – Text‑to‑speech (Microsoft Edge voices)
- `FFmpeg` – Audio playback in Discord
- **Gemini API** (Google Generative Language) – The brain

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/starfall-apk/kulsh.git
cd kulsh
