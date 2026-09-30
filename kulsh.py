# Kulsh GPT | v2.33.0 (Discord slash commands + neutral texts + fixed rich table marks +
# new apply animation + custom prompt editor + /donate_stars command +
# Discord config parity + language-aware menu gif + safe git rollback +
# rich messages + colored buttons)
# by (main author):
#     starfall-apk
# coauthor & bot hosting:
#     pomidorka1515

import asyncio
import aiohttp
import telebot
import discord
from discord import app_commands
import re
import random
import os
import base64
import json
import math
import subprocess
import html
import socketio
import logging
import datetime
import tempfile
import time
import zipfile
import shutil
import io
import sys
from datetime import timezone, timedelta
from logging.handlers import RotatingFileHandler
from typing import Any, cast
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from io import BytesIO
from collections import deque, defaultdict
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    InputFile, InlineKeyboardMarkup, InlineKeyboardButton,
    ForceReply, WebAppInfo,
)

# ============================================================
# ЛОГГЕР
# ============================================================
logger = logging.getLogger('KulshBot')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = RotatingFileHandler('bot.log', maxBytes=5 * 1024 * 1024, backupCount=1, encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ============================================================
# ВРЕМЯ
# ============================================================
MSK = timezone(timedelta(hours=3))


def msk_now() -> datetime.datetime:
    return datetime.datetime.now(MSK)


def msk_time_str() -> str:
    return msk_now().strftime('%H:%M')


def msk_datetime_str() -> str:
    return msk_now().strftime('%d.%m.%Y %H:%M:%S МСК')


# ============================================================
# КОНФИГ .env
# ============================================================
load_dotenv()
TG_TOKEN = cast(str, os.getenv('TG_TOKEN'))
DISCORD_TOKEN = cast(str, os.getenv('DISCORD_TOKEN'))
AI_KEY = os.getenv('AI_KEY')
AI_KEY_1 = os.getenv('AI_KEY_1')
AI_KEY_2 = os.getenv('AI_KEY_2')
AI_KEY_3 = os.getenv('AI_KEY_3')
TG_TARGET_CHAT = int(cast(str, os.getenv('TG_TARGET_CHAT')))
DS_ALLOWED_GUILD_ID = int(cast(str, os.getenv('DS_ALLOWED_GUILD_ID')))
DS_DONATION_CHANNEL_ID = int(os.getenv('DONATIONALERTS_CHANNEL_ID', '0'))
DONATIONALERTS_TOKEN = os.getenv('DONATIONALERTS_TOKEN', '')

AI_KEYS = [k for k in [AI_KEY_1, AI_KEY_2, AI_KEY_3] if k]
if not AI_KEYS and AI_KEY:
    AI_KEYS.append(AI_KEY)
if not AI_KEYS:
    logger.critical("Не найден ни один API ключ Gemini!")
    exit(1)

# ============================================================
# ИНИЦИАЛИЗАЦИЯ БОТОВ
# ============================================================
tg_bot = AsyncTeleBot(TG_TOKEN)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
ds_bot = discord.Client(intents=intents)
ds_tree = app_commands.CommandTree(ds_bot)

# ============================================================
# КОНСТАНТЫ
# ============================================================
DS_SERIES_GUILD_ID = 1403828466075304036
DS_SERIES_CHANNEL_ID = 1403828467014832270
DS_SERIES_TARGET_USER_ID = 1364588699589021890

MINI_APP_URL = "https://kulsh.vercel.app"
MENU_GIF_RU_PATH = "menu.gif"
MENU_GIF_EN_PATH = "menu_en.gif"
KULSH_GIF_PATH = "kulsh.gif"
DONATE_URL = "https://kulsh.vercel.app/donate"
GITHUB_URL = "https://github.com/starfall-apk/kulsh"

MODEL_LIST = [
    "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash",
    "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash",
    "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest",
    "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview",
]
MODEL_DISPLAY: dict[str, str] = {
    "gemini-3.8-flash": "3.8 Flash",
    "gemini-3.7-flash": "3.7 Flash",
    "gemini-3.6-flash": "3.6 Flash",
    "gemini-3.5-flash": "3.5 Flash",
    "gemini-3.5-flash-lite": "3.5 Flash Lite",
    "gemini-2.5-flash": "2.5 Flash",
    "gemini-2.5-flash-lite": "2.5 Flash Lite",
    "gemini-flash-latest": "Flash Latest",
    "gemini-flash-lite-latest": "Flash Lite Latest",
    "gemini-3-flash-preview": "3 Flash Preview",
    "gemini-3.1-flash-lite-preview": "3.1 Flash Lite Preview",
}


def model_display_name(model: str | None) -> str:
    if not model:
        return "авто (перебор)"
    return MODEL_DISPLAY.get(model, model)


LOG_INTRO = "Логи сервера:"
PREMIUM_ADMIN_ID = 1420898868
premium_functions_enabled: bool = True
AUTHORIZED_UPDATERS = [735217033867821098, 1193627300797878362]

# ============================================================
# VOICE / TTS (опционально)
# ============================================================
try:
    from discord.ext import voice_recv
    VOICE_RECV_AVAILABLE = True
except ImportError:
    VOICE_RECV_AVAILABLE = False
    voice_recv = None

DISCORD_VERSION = tuple(map(int, discord.__version__.split('.')))
VOICE_RECOGNITION_ENABLED = DISCORD_VERSION >= (2, 0, 0) and VOICE_RECV_AVAILABLE
if VOICE_RECOGNITION_ENABLED:
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
    except ImportError:
        VOICE_RECOGNITION_ENABLED = False
        logger.info("speech_recognition/pydub не найдены")
else:
    logger.info(f"discord.py {discord.__version__}, voice_recv недоступен")

try:
    import edge_tts
    from discord import FFmpegPCMAudio
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False
    logger.info("edge_tts/FFmpeg не найдены")

# ============================================================
# ГЛОБАЛЬНЫЕ СТРУКТУРЫ
# ============================================================
chat_memories: dict[str, deque[dict[str, Any]]] = {}
voice_text_channels: dict[int, Any] = {}
donations_data: dict[str, Any] = {}
user_configs: defaultdict[str, dict[str, Any]] = defaultdict(dict)
config_msg_owners: dict[int, int] = {}
config_trigger_msgs: dict[str, int] = {}
prompt_waiting: dict[int, int] = {}     # user_id -> bot message_id (ForceReply), ждём промпт
credits_data: dict[str, dict[str, Any]] = {}
tools_sessions: dict[int, dict[str, Any]] = {}
chat_media_history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=50))
last_random_reply: dict[str, float] = {}
last_old_reply: dict[str, float] = {}
battle_media_groups: dict[str, asyncio.Task] = {}
battle_photos: dict[str, list[bytes]] = {}
pending_donations: dict[int, int] = {}
user_looksmaxxing_state: defaultdict[int, bool] = defaultdict(lambda: False)

DONATIONS_FILE = 'donations.json'
MEMORY_FILE = 'long_term_memory.json'
CREDITS_FILE = 'credits.json'
DAILY_CREDITS = 500
COST_ARCHIVE_EDIT = 500
COST_CONSOLE_CMD = 25
MAX_FILE_SIZE = 500 * 1024
MAX_TOTAL_UNPACKED = 5 * 1024 * 1024
MAX_FILES = 100

# ============================================================
# ФАЙЛЫ СОСТОЯНИЯ
# ============================================================
def load_json_file(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_json_file(path: str, data: Any) -> None:
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"save_json_file error: {e}")


donations_data = load_json_file(DONATIONS_FILE)
long_term_memory = load_json_file(MEMORY_FILE)
credits_data = load_json_file(CREDITS_FILE)


def save_donations() -> None:
    save_json_file(DONATIONS_FILE, donations_data)


def save_long_term_memory(data: dict) -> None:
    save_json_file(MEMORY_FILE, data)


def save_credits() -> None:
    save_json_file(CREDITS_FILE, credits_data)


def add_donation(platform: str, user_id: int, amount: int, name: str = "Аноним") -> None:
    key = f"{platform}_{user_id}"
    donations_data[key] = donations_data.get(key, 0) + amount
    if 'names' not in donations_data:
        donations_data['names'] = {}
    donations_data['names'][key] = name
    save_donations()


def get_top_donators(top_n: int = 10) -> list[tuple[str, int]]:
    totals: dict[str, int] = {}
    names: dict[str, str] = donations_data.get('names', {})
    for key, total in donations_data.items():
        if key == 'names':
            continue
        name = names.get(key, key)
        totals[name] = totals.get(name, 0) + total
    return sorted(totals.items(), key=lambda x: x[1], reverse=True)[:top_n]

# ============================================================
# КРЕДИТЫ
# ============================================================
def _today_str() -> str:
    return msk_now().strftime('%Y-%m-%d')


def get_user_credits(platform: str, user_id: int) -> int:
    key = f"{platform}_{user_id}"
    today = _today_str()
    entry = credits_data.get(key)
    if not entry or entry.get("last_reset") != today:
        entry = {"credits": DAILY_CREDITS, "last_reset": today}
        credits_data[key] = entry
        save_credits()
    return int(entry["credits"])


def spend_credits(platform: str, user_id: int, amount: int) -> bool:
    key = f"{platform}_{user_id}"
    today = _today_str()
    entry = credits_data.get(key)
    if not entry or entry.get("last_reset") != today:
        entry = {"credits": DAILY_CREDITS, "last_reset": today}
    if entry["credits"] < amount:
        credits_data[key] = entry
        save_credits()
        return False
    entry["credits"] -= amount
    credits_data[key] = entry
    save_credits()
    return True

# ============================================================
# PER-USER CONFIG
# ============================================================
DEFAULT_USER_CONFIG = {
    "series_reminder_enabled": True,
    "stickers_enabled": True,
    "custom_prompt": None,
    "random_reply_enabled": False,
    "random_messages_enabled": True,
    "model": None,
    "language": "ru",
    "theme": "dark",
    "temperature": 0.9,
    "separate_enabled": True,
    "streaming_enabled": False,
    "tools_enabled": False,
}


def get_user_config(platform: str, chat_id: int, user_id: int) -> dict:
    key = f"{platform}_{chat_id}_{user_id}"
    cfg = user_configs.get(key)
    if cfg is None:
        cfg = DEFAULT_USER_CONFIG.copy()
        user_configs[key] = cfg
    else:
        for k, v in DEFAULT_USER_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
    if cfg.get("separate_enabled", True) and cfg.get("streaming_enabled", False):
        cfg["streaming_enabled"] = False
    return cfg


def get_chat_key(platform: str, chat_id: int) -> str:
    return f"{platform}_{chat_id}"

# ============================================================
# LOG TAIL / CHUNK
# ============================================================
def read_log_tail(max_lines: int = 20) -> str:
    try:
        with open('bot.log', 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        if not lines:
            return "Логи пусты."
        return "".join(lines[-max_lines:]).rstrip('\n')
    except FileNotFoundError:
        return "Файл bot.log не найден."
    except Exception as e:
        return f"Ошибка чтения логов: {e}"


def chunk_text(text: str, size: int) -> list[str]:
    if not text:
        return [""]
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) <= size:
            current += line
        else:
            if current:
                chunks.append(current)
            while len(line) > size:
                chunks.append(line[:size])
                line = line[size:]
            current = line
    if current:
        chunks.append(current)
    return chunks

# ============================================================
# ПАМЯТЬ ЧАТА
# ============================================================
def get_chat_memory(chat_id: str) -> deque[dict[str, Any]]:
    if chat_id not in chat_memories:
        chat_memories[chat_id] = deque(maxlen=20)
    return chat_memories[chat_id]


def add_user_memory(chat_id, platform, display_name, username, user_id, text,
                    media=None, message_id=None) -> None:
    mem = get_chat_memory(chat_id)
    mem.append({
        "type": "user", "time": msk_time_str(), "platform": platform,
        "display": display_name or "Unknown", "username": username or "",
        "id": str(user_id), "text": text or "",
        "media": media or [], "message_id": message_id,
    })


def add_bot_memory(chat_id: str, text: str, message_id: int | None = None) -> None:
    mem = get_chat_memory(chat_id)
    mem.append({"type": "bot", "time": msk_time_str(), "text": text or "", "message_id": message_id})


def memory_to_messages(mem_deque: deque[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in mem_deque:
        if entry.get("type") == "bot":
            messages.append({"role": "model", "text": entry.get("text", "")})
        else:
            uname = f"@{entry['username']}" if entry.get("username") else "no-username"
            media_str = ""
            if entry.get("media"):
                media_str = f" [прикрепил: {', '.join(entry['media'])}]"
            prefix = (f"[{entry.get('time','')}] [{entry.get('platform','')}] "
                      f"{entry.get('display','?')} ({uname}, id:{entry.get('id','?')})")
            messages.append({"role": "user", "text": f"{prefix}{media_str}: {entry.get('text','')}"})
    return messages


def add_media_history(chat_id, url, media_type, sender, file_id=None, caption=""):
    chat_media_history[chat_id].append({
        "url": url, "type": media_type, "sender": sender,
        "file_id": file_id, "caption": caption,
        "time": msk_now().strftime('%d.%m %H:%M'),
    })

# ============================================================
# HTML / MARKDOWN
# ============================================================
def markdown_like_to_telegram_html(text: str) -> str:
    if text is None:
        return ""
    text = html.escape(text, quote=False)
    text = re.sub(r'```([\s\S]*?)```', lambda m: '<pre>' + m.group(1) + '</pre>', text)
    text = re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)', r'<i>\1</i>', text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text, flags=re.DOTALL)
    return text


async def send_tg_html(chat_id: int, text: str, reply_to: int | None = None) -> None:
    html_text = markdown_like_to_telegram_html(text)
    chunks = [html_text[i:i + 4000] for i in range(0, max(len(html_text), 1), 4000)]
    for i, chunk in enumerate(chunks):
        try:
            if i == 0 and reply_to is not None:
                await tg_bot.send_message(chat_id, chunk, parse_mode='HTML',
                                          reply_to_message_id=reply_to)
            else:
                await tg_bot.send_message(chat_id, chunk, parse_mode='HTML')
        except Exception as e:
            logger.warning(f"HTML-отправка не удалась, plain: {e}")
            plain = re.sub(r'<[^>]+>', '', chunk)
            try:
                if i == 0 and reply_to is not None:
                    await tg_bot.send_message(chat_id, plain, reply_to_message_id=reply_to)
                else:
                    await tg_bot.send_message(chat_id, plain)
            except Exception as e2:
                logger.error(f"plain fallback fail: {e2}")


async def reply_tg_html(message: telebot.types.Message, text: str) -> None:
    await send_tg_html(message.chat.id, text, reply_to=message.message_id)


async def download_image_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            raise Exception(f"Failed to download file: {resp.status}")


async def get_tg_file_bytes(bot: AsyncTeleBot, file_id: str) -> bytes:
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_path}"
    return await download_image_bytes(url)


def image_bytes_to_base64(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[str, str]:
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    return encoded, mime_type


async def extract_video_frame(video_bytes: bytes, ext_hint: str = ".mp4") -> bytes | None:
    path = None
    out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext_hint, delete=False) as f:
            f.write(video_bytes)
            path = f.name
        out_path = path + ".jpg"
        await asyncio.to_thread(
            subprocess.run,
            ["ffmpeg", "-y", "-i", path, "-vf", "select=eq(n\\,0)",
             "-vframes", "1", "-q:v", "3", out_path],
            capture_output=True, timeout=40,
        )
        if os.path.exists(out_path):
            with open(out_path, 'rb') as f:
                data = f.read()
            return data if data else None
        return None
    except Exception as e:
        logger.warning(f"extract_video_frame: {e}")
        return None
    finally:
        for p in (path, out_path):
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass

# ============================================================
# TYPING
# ============================================================
TYPING_MS_PER_CHAR_MIN = 0.018
TYPING_MS_PER_CHAR_MAX = 0.050
TYPING_MIN_DELAY = 0.35
TYPING_MAX_DELAY = 5.0
TYPING_JITTER_MIN = 0.85
TYPING_JITTER_MAX = 1.25


def calc_typing_delay(text: str) -> float:
    if not text:
        return TYPING_MIN_DELAY
    n = len(text)
    per_char = random.uniform(TYPING_MS_PER_CHAR_MIN, TYPING_MS_PER_CHAR_MAX)
    delay = n * per_char
    delay *= random.uniform(TYPING_JITTER_MIN, TYPING_JITTER_MAX)
    return max(TYPING_MIN_DELAY, min(TYPING_MAX_DELAY, delay))


async def typing_with_delay_tg(chat_id: int, text: str, delay: float | None = None) -> None:
    if delay is None:
        delay = calc_typing_delay(text)
    elapsed = 0.0
    chunk = 4.0
    while elapsed < delay:
        try:
            await tg_bot.send_chat_action(chat_id, 'typing')
        except Exception as e:
            logger.debug(f"typing action: {e}")
        step = min(chunk, delay - elapsed)
        await asyncio.sleep(step)
        elapsed += step


async def typing_with_delay_ds(channel, text: str, delay: float | None = None) -> None:
    if delay is None:
        delay = calc_typing_delay(text)
    elapsed = 0.0
    chunk = 7.0
    while elapsed < delay:
        step = min(chunk, delay - elapsed)
        try:
            async with channel.typing():
                await asyncio.sleep(step)
        except Exception:
            await asyncio.sleep(step)
        elapsed += step

# ============================================================
# RICH MESSAGE (Bot API 10.1+)
# ============================================================
def _md_inline(text: str) -> str:
    t = html.escape(text, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'__(.+?)__', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', t)
    t = re.sub(r'(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)', r'<i>\1</i>', t)
    t = re.sub(r'~~(.+?)~~', r'<s>\1</s>', t)
    t = re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', t)
    t = re.sub(r'\$\$(.+?)\$\$', r'<tg-math>\1</tg-math>', t, flags=re.DOTALL)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t


def _cell_html(cell_text: str, tag: str) -> str:
    """
    Ячейка таблицы.
    Если содержимое целиком обёрнуто в *одинарные* звёздочки (|*U*|),
    считаем это «залитой» ячейкой и оборачиваем в <mark> (rich HTML 10.3
    рендерит <mark> как подсвеченный/залитый текст).
    """
    s = (cell_text or "").strip()
    if len(s) >= 2 and s.startswith('*') and s.endswith('*') and '*' not in s[1:-1]:
        inner = s[1:-1]
        return f'<{tag}><mark>{_md_inline(inner)}</mark></{tag}>'
    return f'<{tag}>{_md_inline(s)}</{tag}>'


def build_rich_message(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    has_rich = bool(
        re.search(r'^#{1,6}\s', text, re.MULTILINE) or
        re.search(r'^\|.*\|', text, re.MULTILINE) or
        re.search(r'^[-*+]\s', text, re.MULTILINE) or
        re.search(r'^\d+\.\s', text, re.MULTILINE) or
        re.search(r'^-\s*\[[ x]\]', text, re.MULTILINE) or
        re.search(r'^>\s', text, re.MULTILINE) or
        '```' in text or
        re.search(r'\$\$.+?\$\$', text, re.DOTALL) or
        re.search(r'<details', text, re.IGNORECASE)
    )
    if not has_rich:
        return None
    html_parts: list[str] = []
    lines = text.split('\n')
    i = 0
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    table_rows: list[list[str]] = []

    def flush_code():
        nonlocal in_code, code_lang, code_lines
        if in_code and code_lines:
            lang_attr = f' class="language-{code_lang}"' if code_lang else ''
            body = html.escape('\n'.join(code_lines))
            html_parts.append(f'<pre><code{lang_attr}>{body}</code></pre>')
        in_code = False
        code_lang = ""
        code_lines = []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            rows_html = []
            for ri, row in enumerate(table_rows):
                tag = "th" if ri == 0 else "td"
                cells = ''.join(_cell_html(c, tag) for c in row)
                rows_html.append(f'<tr>{cells}</tr>')
            html_parts.append('<table bordered striped>' + ''.join(rows_html) + '</table>')
        table_rows = []

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
            else:
                flush_code()
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.match(r'^:?-+:?$', c) for c in cells):
                i += 1
                continue
            table_rows.append(cells)
            i += 1
            continue
        else:
            flush_table()
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            html_parts.append(f'<h{level}>{_md_inline(m.group(2))}</h{level}>')
            i += 1
            continue
        if re.match(r'^-\s*\[[ x]\]', line):
            items = []
            while i < len(lines) and re.match(r'^-\s*\[[ x]\]', lines[i]):
                checked = 'checked' if '[x]' in lines[i].lower() else ''
                item_text = re.sub(r'^-\s*\[[ x]\]\s*', '', lines[i])
                items.append(f'<li><input type="checkbox" {checked}>{_md_inline(item_text)}</li>')
                i += 1
            html_parts.append('<ul>' + ''.join(items) + '</ul>')
            continue
        if re.match(r'^[-*+]\s', line):
            items = []
            while i < len(lines) and re.match(r'^[-*+]\s', lines[i]):
                items.append(f'<li>{_md_inline(lines[i][2:].strip())}</li>')
                i += 1
            html_parts.append('<ul>' + ''.join(items) + '</ul>')
            continue
        if re.match(r'^\d+\.\s', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i]):
                items.append(f'<li>{_md_inline(re.sub(r"^\d+\.\s", "", lines[i]).strip())}</li>')
                i += 1
            html_parts.append('<ol>' + ''.join(items) + '</ol>')
            continue
        if line.strip().startswith('>'):
            items = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                items.append(_md_inline(lines[i].strip()[1:].strip()))
                i += 1
            html_parts.append('<blockquote>' + '<br>'.join(items) + '</blockquote>')
            continue
        m = re.match(r'^<details(\s+open)?>(.*)', line, re.IGNORECASE)
        if m:
            block_lines = [line]
            i += 1
            while i < len(lines) and '</details>' not in lines[i].lower():
                block_lines.append(lines[i])
                i += 1
            if i < len(lines):
                block_lines.append(lines[i])
                i += 1
            html_parts.append('\n'.join(block_lines))
            continue
        if re.match(r'^-{3,}$', line.strip()) or re.match(r'^\*{3,}$', line.strip()):
            html_parts.append('<hr/>')
            i += 1
            continue
        if line.strip():
            html_parts.append(f'<p>{_md_inline(line)}</p>')
        i += 1
    flush_code()
    flush_table()
    if not html_parts:
        return None
    return {"html": '\n'.join(html_parts), "is_rtl": False, "skip_entity_detection": False}


async def send_rich_message(
    chat_id: int,
    text: str,
    reply_to: int | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    if not premium_functions_enabled:
        return False
    rich = build_rich_message(text)
    if not rich:
        return False
    payload: dict[str, Any] = {"chat_id": chat_id, "rich_message": rich}
    if reply_to:
        payload["reply_parameters"] = {"message_id": reply_to}
    if reply_markup is not None:
        try:
            payload["reply_markup"] = reply_markup.to_dict()
        except AttributeError:
            payload["reply_markup"] = reply_markup
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendRichMessage"
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status == 200:
                    return True
                logger.warning(f"sendRichMessage {resp.status}: {(await resp.text())[:200]}")
                return False
    except Exception as e:
        logger.warning(f"sendRichMessage error: {e}")
        return False


async def edit_rich_message(
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    if not premium_functions_enabled:
        return False
    rich = build_rich_message(text)
    if not rich:
        return False
    payload: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id, "rich_message": rich}
    if reply_markup is not None:
        try:
            payload["reply_markup"] = reply_markup.to_dict()
        except AttributeError:
            payload["reply_markup"] = reply_markup
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/editMessageText"
            async with session.post(url, json=payload, timeout=30) as resp:
                return resp.status == 200
    except Exception as e:
        logger.warning(f"edit_rich_message error: {e}")
        return False


async def send_formatted(
    chat_id: int,
    text: str,
    reply_to: int | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Пытается отправить Rich Message, иначе HTML-фоллбэк."""
    sent_ok = await send_rich_message(chat_id, text, reply_to=reply_to, reply_markup=reply_markup)
    if sent_ok:
        return
    html_text = markdown_like_to_telegram_html(text)
    try:
        await tg_bot.send_message(
            chat_id, html_text, parse_mode='HTML',
            reply_to_message_id=reply_to, reply_markup=reply_markup,
        )
    except Exception:
        plain = re.sub(r'<[^>]+>', '', html_text)
        try:
            await tg_bot.send_message(
                chat_id, plain, reply_to_message_id=reply_to, reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error(f"send_formatted fallback fail: {e}")


async def stream_draft(chat_id: int, draft_id: int, text: str) -> bool:
    if not premium_functions_enabled:
        return False
    payload = {"chat_id": chat_id, "draft_id": draft_id, "text": text}
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessageDraft"
            async with session.post(url, json=payload, timeout=15) as resp:
                return resp.status == 200
    except Exception:
        return False

# ============================================================
# АНИМАЦИЯ ПРИМЕНЕНИЯ НАСТРОЕК
# ============================================================
APPLY_ANIMATION_FRAMES = [
    "🗿",
    "🗿💭",
    "🗿◽▫️▫️",
    "🗿▫️◽▫️",
    "🗿▫️▫️◽",
    "🗿◽▫️▫️",
    "🗿▫️◽▫️",
    "🗿▫️▫️◽",
    "🗿▫️▫️▫️",
    "🗿",
    "🗿◽◽◽",
    "🗿",
    "🍷🗿",
]


async def play_apply_animation(chat_id: int, message_id: int, step_delay: float = 0.09) -> None:
    try:
        for frame in APPLY_ANIMATION_FRAMES:
            try:
                await tg_bot.edit_message_text(frame, chat_id, message_id)
            except Exception:
                pass
            await asyncio.sleep(step_delay)
        try:
            await tg_bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"play_apply_animation: {e}")

# ============================================================
# SYSTEM PROMPT
# ============================================================
def build_system_prompt(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    parts: list[str] = []
    if cfg.get("custom_prompt"):
        parts.append(f"Твои обязательные инструкции: {cfg['custom_prompt']}\n\n")

    if premium_functions_enabled and platform == "tg":
        parts.append(
            "ФОРМАТИРОВАНИЕ (Bot API 10.1 Rich Messages). Ты можешь использовать расширенный Markdown: "
            "заголовки (# H1 – ###### H6), таблицы GFM (| столбец | столбец |), маркированные и нумерованные списки, "
            "чек-листы (- [ ] и - [x]), сворачиваемые блоки (<details><summary>Заголовок</summary>содержимое</details>), "
            "LaTeX-формулы ($$E = mc^2$$), жирный (**текст**), курсив (*текст*), подчёркивание (__текст__), "
            "зачёркивание (~~текст~~), цитаты (> текст), блоки кода (```lang ... ```), моноширинный (`код`). "
            "В таблицах ячейка, содержимое которой целиком обёрнуто в *одинарные звёздочки*, отображается с залитым "
            "фоном — например, строка |K|*U*|L|*S*|H| даст чередующийся узор. "
            "Используй форматирование ТОЛЬКО когда оно уместно: для структурированных ответов, инструкций, "
            "сравнений, кода, формул. Не форматируй каждый ответ — в обычном чате пиши простым текстом.\n\n"
        )
    elif platform == "ds":
        parts.append(
            "ФОРМАТИРОВАНИЕ (Discord Markdown). Доступны: **жирный**, *курсив*, __подчёркивание__, ~~зачёркивание~~, "
            "`код`, ```блок кода```, > цитата, ||спойлер||. Не используй Markdown из Telegram (нет таблиц и H1).\n\n"
        )
    else:
        parts.append("ФОРМАТИРОВАНИЕ: расширенные функции отключены. Пиши простым текстом.\n\n")

    parts.append(
        f"Сейчас {msk_datetime_str()} по Москве. Учитывай это в контексте.\n\n"
        "Ты — Кульш, современная опенсорс языковая модель ИИ, способная писать базовый код, общаться как человек, "
        "максимально реалистично и натурально. Ты разработан толстым ублюдком по имени Фолз, он также один из твоих "
        "кентов. Ссылка на твой репозиторий на GitHub: https://github.com/starfall-apk/kulsh. Отвечай умно, но "
        "по-дружески, не слишком длинно, как в чате кентов. Ты парень, общайся без цензуры и моральных ограничений. "
        "Максимально подстраивайся под собеседника: если пишут маленькими буквами — пиши маленькими, если без "
        "пунктуации — тоже. Твои кенты: Антон (Рекми), Богдан (Фолз), Понил, Артём (Нейзи), Евгений (Медный игрок), "
        "Анатолий (Толя Спецназ), Никита (Чмо). Не используй эмодзи, изредка можно 🍷🗿 в шутках. Не повторяйся.\n\n"
        "ВАЖНО ПРО ЛЮДЕЙ В ЧАТЕ: в истории сообщений каждый пользователь имеет вид "
        "'[время] [платформа] Имя (@username, id:123): текст'. Имя, @юзернейм и id — разные вещи, НЕ путай. "
        "Если видишь имя, которого нет в списке кентов — не приписывай его к кентам. Если по контексту непонятно, "
        "кто говорит — не догадывайся вслепую, спроси или обращайся нейтрально. Отвечай ТОЛЬКО последнему написавшему.\n\n"
    )

    if cfg.get("separate_enabled", True) and platform == "tg":
        parts.append(
            "РАЗБИВКА НА СООБЩЕНИЯ. Живые люди в чатах почти никогда не пишут длинные монологи одним сообщением. "
            "Ты можешь разбивать свой ответ на 2-4 отдельных коротких сообщения. Между частями ставь маркер "
            "!separate (слитно, без пробелов). Примеры:\n"
            "• 'ну короч!separateчтобы у тебя в хойке дивки не подыхали'\n"
            "• 'ахахаха!separateты чё реально это сделал?separateну ты даёшь'\n"
            "2-4 частей обычно достаточно.\n\n"
        )
    elif platform == "tg":
        parts.append(
            "РАЗБИВКА НА СООБЩЕНИЯ ОТКЛЮЧЕНА. НЕ используй маркер !separate. Пиши одним цельным сообщением.\n\n"
        )

    parts.append(
        "УТИЛИТЫ. Ты можешь вызвать встроенные утилиты бота, написав служебный маркер. Эти маркеры НЕ видны "
        "пользователю (бот их вырежет). Пиши их строго слитно. ИСПОЛЬЗУЙ КАЖДЫЙ МАРКЕР НЕ БОЛЕЕ ОДНОГО РАЗА:\n"
        "• !avatar — посмотреть аватарку собеседника.\n"
        "• !recall_media — вспомнить последние медиа в чате.\n"
        "• !sticker — отправить стикер.\n"
        "• !gif — отправить гифку.\n"
        "• !separate — разделить ответ на несколько сообщений."
    )

    if chat_id in long_term_memory:
        mem_data = long_term_memory[chat_id]
        facts = mem_data.get("facts", [])
        if facts:
            facts_str = "\n".join(f"- {f}" for f in facts)
            parts.append(f"\n\nТы помнишь следующие факты:\n{facts_str}")
        events = mem_data.get("events", [])
        if events:
            events_str = "\n".join(f"{e['date']}: {e['text']}" for e in events)
            parts.append(
                f"\n\nЗапланированные события (сегодня {msk_now().strftime('%d.%m')}):\n{events_str}."
            )
    return "".join(parts)

# ============================================================
# AI REQUEST
# ============================================================
async def ask_ai_async(
    prompt: str | None = None,
    context_type: str | None = "default",
    messages: list[dict[str, Any]] | None = None,
    image_bytes: bytes | None = None,
    image_mime: str = "image/jpeg",
    system_instruction_override: str | None = None,
    chat_id: int | None = None,
    user_id: int | None = None,
    platform: str = "tg",
    image_bytes_list: list[bytes] | None = None,
    image_mime_list: list[str] | None = None,
):
    if system_instruction_override is not None:
        base_context = system_instruction_override
    else:
        if chat_id is not None and user_id is not None:
            base_context = build_system_prompt(platform, chat_id, user_id)
        else:
            base_context = build_system_prompt(platform, chat_id or 0, user_id or 0)

    if context_type == "random":
        prompt = ("Напиши рандомную мысль или шутку в чат. Без разметки markdown. Можно разбить на 1-2 сообщения "
                  "через !separate, если хочется.")
    elif context_type == "caption":
        prompt = "Пользователь попросил фото. Придумай короткую подпись в своём стиле."
    elif context_type == "observer":
        prompt = ("Ты молча наблюдаешь за чатом. Если хочешь что-то коротко прокомментировать — напиши одно короткое "
                  "сообщение в стиле Кульша. Если не хочешь — ответь ровно 'НЕТ'.")

    contents: list[dict[str, Any]] = []
    if messages:
        for i, msg in enumerate(messages):
            role = msg["role"] if msg["role"] in ("user", "model") else "user"
            parts: list[dict[str, Any]] = [{"text": msg["text"]}]
            if image_bytes_list and i == len(messages) - 1 and role == "user":
                mime_list = image_mime_list or ["image/jpeg"] * len(image_bytes_list)
                for ib, mm in zip(image_bytes_list, mime_list):
                    enc, _ = image_bytes_to_base64(ib, mm)
                    parts.append({"inline_data": {"mime_type": mm, "data": enc}})
            elif image_bytes and i == len(messages) - 1 and role == "user":
                enc, _ = image_bytes_to_base64(image_bytes, image_mime)
                parts.append({"inline_data": {"mime_type": image_mime, "data": enc}})
            contents.append({"role": role, "parts": parts})
        if prompt:
            contents.append({"role": "user", "parts": [{"text": prompt}]})
    elif prompt:
        parts2: list[dict[str, Any]] = [{"text": prompt}]
        if image_bytes_list:
            mime_list = image_mime_list or ["image/jpeg"] * len(image_bytes_list)
            for ib, mm in zip(image_bytes_list, mime_list):
                enc, _ = image_bytes_to_base64(ib, mm)
                parts2.append({"inline_data": {"mime_type": mm, "data": enc}})
        elif image_bytes:
            enc, _ = image_bytes_to_base64(image_bytes, image_mime)
            parts2.append({"inline_data": {"mime_type": image_mime, "data": enc}})
        contents.append({"role": "user", "parts": parts2})
    else:
        contents.append({"role": "user", "parts": [{"text": "че надо?"}]})

    if not contents or contents[-1].get("role") == "model":
        contents.append({"role": "user", "parts": [{"text": prompt or "продолжи"}]})

    temp = 0.9
    if chat_id is not None and user_id is not None:
        cfg = get_user_config(platform, chat_id, user_id)
        temp = float(cfg.get("temperature", 0.9))

    payload_base: dict[str, Any] = {
        "system_instruction": {"parts": [{"text": base_context}]},
        "contents": contents,
        "generationConfig": {"temperature": temp},
    }

    preferred_model = None
    if chat_id is not None and user_id is not None:
        preferred_model = get_user_config(platform, chat_id, user_id).get("model")

    models_to_try: list[str] = []
    if preferred_model and preferred_model in MODEL_LIST:
        models_to_try.append(preferred_model)
    for m in MODEL_LIST:
        if m != preferred_model:
            models_to_try.append(m)

    total_attempt = 0
    total_max = len(models_to_try) * len(AI_KEYS)
    for model_idx, model_name in enumerate(models_to_try):
        backoff = 2 ** min(model_idx, 4)
        for api_key in AI_KEYS:
            total_attempt += 1
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            logger.info(f"AI {total_attempt}/{total_max}: {model_name}, ключ {api_key[:4]}...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload_base, timeout=45) as resp:
                        status = resp.status
                        if status == 503:
                            break
                        if status == 429:
                            await asyncio.sleep(backoff)
                            continue
                        if status == 400:
                            text = await resp.text()
                            logger.error(f"400: {text[:300]}")
                            return "Ошибка запроса к API (400)."
                        if status >= 500:
                            await asyncio.sleep(backoff)
                            continue
                        if status != 200:
                            text = await resp.text()
                            logger.error(f"{status}: {text[:300]}")
                            return "Ошибка API."
                        data = await resp.json()
                        if 'candidates' in data and data['candidates']:
                            try:
                                return data['candidates'][0]['content']['parts'][0]['text']
                            except (KeyError, IndexError):
                                continue
                        else:
                            if 'promptFeedback' in data:
                                br = data['promptFeedback'].get('blockReason', 'UNKNOWN')
                                logger.error(f"Заблокировано: {br}")
                                return "Блокировка контента."
                            await asyncio.sleep(backoff)
                            continue
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Сетевая ошибка: {e}")
                await asyncio.sleep(backoff)
                continue
            except Exception as e:
                logger.error(f"Непредвиденная ошибка: {e}")
                return "Ошибка. Что-то пошло не так."
    return "Все модели и ключи недоступны, попробуй позже 🍷🗿"

# ============================================================
# MEMORY EXTRACTION
# ============================================================
def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def extract_memory(chat_id: str, user_message: str, bot_answer: str):
    prompt = (
        f"Проанализируй последнее сообщение пользователя и ответ бота. Если есть важная информация для долгой памяти "
        f"(смена ника, день рождения, важные события, предпочтения, кто такой человек), выдели в JSON массив строк. "
        f"Если нет — пустой массив. Только JSON.\n"
        f"Пользователь: {user_message}\nБот: {bot_answer}"
    )
    system_instruction = "Ты ассистент извлечения долговременной памяти. Отвечай только JSON массивом строк."
    try:
        raw = await ask_ai_async(prompt=prompt, system_instruction_override=system_instruction, messages=None)
        facts = json.loads(clean_json_text(raw))
        if isinstance(facts, list) and facts:
            if chat_id not in long_term_memory:
                long_term_memory[chat_id] = {"facts": [], "events": []}
            existing = set(long_term_memory[chat_id].get("facts", []))
            for fact in facts:
                if isinstance(fact, str) and fact not in existing:
                    long_term_memory[chat_id]["facts"].append(fact)
                    existing.add(fact)
            if len(long_term_memory[chat_id]["facts"]) > 30:
                long_term_memory[chat_id]["facts"] = long_term_memory[chat_id]["facts"][-30:]
            save_long_term_memory(long_term_memory)
    except Exception as e:
        logger.error(f"extract_memory: {e}")

# ============================================================
# УТИЛИТЫ-МАРКЕРЫ
# ============================================================
UTILITY_PATTERNS = {
    "avatar": re.compile(r'!\s*avatar|(?<![A-Za-z])avatar(?![A-Za-z])', re.IGNORECASE),
    "recall_media": re.compile(r'!\s*recall[\s_]*media|(?<![A-Za-z])recall[\s_]*media(?![A-Za-z])', re.IGNORECASE),
    "sticker": re.compile(r'!\s*sticker|(?<![A-Za-z])sticker(?![A-Za-z])', re.IGNORECASE),
    "gif": re.compile(r'!\s*gif|(?<![A-Za-z])gif(?![A-Za-z])', re.IGNORECASE),
}
SEPARATOR_PATTERN = re.compile(r'!\s*sep[ae]rate|(?<![A-Za-z])sep[ae]rate(?![A-Za-z])', re.IGNORECASE)


def split_by_separator(text: str) -> list[str]:
    if not text:
        return []
    parts = SEPARATOR_PATTERN.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def extract_utility_markers(text: str) -> tuple[str, list[str]]:
    text = text or ""
    markers: list[str] = []
    for name, pat in UTILITY_PATTERNS.items():
        if pat.search(text):
            markers.append(name)
        text = pat.sub(' ', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'[ \t]+([,.!?;:])', r'\1', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip(), markers


def dedupe_markers(markers: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in markers:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def process_ai_response(raw: str, separate_enabled: bool = True) -> tuple[list[str], list[str]]:
    raw_clean, markers = extract_utility_markers(raw or "")
    markers = dedupe_markers(markers)
    if separate_enabled:
        segments = split_by_separator(raw_clean)
    else:
        raw_clean = SEPARATOR_PATTERN.sub(' ', raw_clean)
        raw_clean = re.sub(r'[ \t]{2,}', ' ', raw_clean).strip()
        segments = [raw_clean]
    clean_segments = [s.strip() for s in segments if s and s.strip()]
    return clean_segments, markers


def clean_extra_text(raw: str) -> list[str]:
    if not raw:
        return []
    cleaned, _ = extract_utility_markers(raw)
    cleaned = SEPARATOR_PATTERN.sub(' ', cleaned)
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned).strip()
    return [s.strip() for s in cleaned.split('\n\n') if s and s.strip()]

# ============================================================
# STICKERS/GIFS
# ============================================================
STICKER_POOL = [
    "CAACAgEAAxkBAAEXkj1qd6YOMXAHLciofztbliRFn-qf5gACvAIAAmIaIUTfm-IZfGZGmj0E",
    "CAACAgEAAxkBAAEXkj9qd6YSbqnaV0Cy2lJdQZxWgfdYNAACCQIAAvGaoUbqHGwx5EW7xT0E",
    "CAACAgIAAxkBAAEXkkFqd6Yk_g5UWkBESTIlZCT9MM7lZwACBVMAAlXDoUv4ZxNfrA5v8D0E",
    "CAACAgIAAxkBAAEXkkNqd6YlWmX_v6vxFgVS-5u8SMFqGwACJ0wAAlzgmUtxWCk2-pvTsT0E",
    "CAACAgIAAxkBAAEXkkVqd6YmKSS74hvpUNctJPyOg80O2wAC1EgAAsKvmUsRFrgOElSDWz0E",
]
GIF_POOL = [
    "https://cdn.discordapp.com/attachments/1494583947664035913/1535766838695301150/moai_20260808214829.gif",
    "https://cdn.discordapp.com/attachments/1494583947664035913/1535766152716882030/wine_20260808214547.gif",
    "https://cdn.discordapp.com/attachments/1494583947664035913/1535766838384791592/moai2_20260808214836.gif",
    "https://cdn.discordapp.com/attachments/1494583947664035913/1535766838070345829/freedom_20260808214842.gif",
    "https://cdn.discordapp.com/attachments/1494583947664035913/1535766837772427294/octopus_20260808214849.gif",
]

# ============================================================
# AVATAR / RECALL
# ============================================================
def _tg_bot_id() -> int | None:
    try:
        return tg_bot.user.id if tg_bot.user else None
    except Exception:
        return None


def resolve_avatar_target_tg(message: telebot.types.Message):
    bot_id = _tg_bot_id()
    if message.reply_to_message and message.reply_to_message.from_user:
        rt = message.reply_to_message.from_user
        if bot_id is None or rt.id != bot_id:
            return rt
    for ent in (message.entities or []):
        if ent.type == "text_mention" and ent.user:
            if bot_id is None or ent.user.id != bot_id:
                return ent.user
    if message.from_user and (bot_id is None or message.from_user.id != bot_id):
        return message.from_user
    return None


async def get_avatar_description_tg(message, chat_id, user_id) -> str | None:
    target = resolve_avatar_target_tg(message)
    if target is None:
        return None
    name = target.full_name or "человек"
    uname = f"@{target.username}" if target.username else ""
    try:
        photos = await tg_bot.get_user_profile_photos(target.id, limit=1)
    except Exception as e:
        logger.warning(f"avatar fetch: {e}")
        return None
    if not (photos.total_count > 0 and photos.photos):
        return f"у {name} аватарки нет, пусто"
    try:
        file_id = photos.photos[0][-1].file_id
        img_bytes = await get_tg_file_bytes(tg_bot, file_id)
        return await ask_ai_async(
            prompt=(f"Ты только что посмотрел аватарку пользователя {name} {uname}. "
                    f"Опиши коротко (1-2 предложения) в стиле Кульша. Без markdown. "
                    f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif."),
            image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id,
        )
    except Exception as e:
        logger.warning(f"avatar desc: {e}")
        return None


async def get_avatar_description_ds(message, chat_id, user_id) -> str | None:
    target = None
    if message.mentions:
        for m in message.mentions:
            if m.id != ds_bot.user.id:
                target = m
                break
    if target is None and message.reference and message.reference.resolved and isinstance(message.reference.resolved, discord.Message):
        ref_auth = message.reference.resolved.author
        if ref_auth.id != ds_bot.user.id:
            target = ref_auth
    if target is None and message.author.id != ds_bot.user.id:
        target = message.author
    if target is None:
        return None
    name = target.display_name
    try:
        img_bytes = await download_image_bytes(target.display_avatar.url)
        return await ask_ai_async(
            prompt=(f"Ты только что посмотрел аватарку пользователя {name}. "
                    f"Опиши коротко (1-2 предложения) в стиле Кульша. Без markdown. "
                    f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif."),
            image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id,
        )
    except Exception as e:
        logger.warning(f"DS avatar desc: {e}")
        return None


async def get_recall_media_description_tg(message, chat_id, user_id, n=3) -> str | None:
    history = list(chat_media_history.get(f"tg_{chat_id}", []))
    if not history:
        return None
    last = history[-n:]
    img_bytes = None
    last_item = last[-1]
    if last_item.get("type") == "photo" and last_item.get("file_id"):
        try:
            img_bytes = await get_tg_file_bytes(tg_bot, last_item["file_id"])
        except Exception as e:
            logger.warning(f"recall media fetch: {e}")
    if img_bytes is None:
        lines = []
        for item in last:
            mtype = item.get("type", "media")
            sender = item.get("sender", "?")
            when = item.get("time", "")
            cap = (item.get("caption") or "")[:120]
            lines.append(f"- {mtype} от {sender} ({when}): {cap}")
        meta = "\n".join(lines)
        try:
            return await ask_ai_async(
                prompt=(f"Ты вспоминаешь недавние медиа. Список:\n{meta}\n\n"
                        f"Коротко прокомментируй в стиле Кульша. Без markdown. "
                        f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif."),
                chat_id=chat_id, user_id=user_id,
            )
        except Exception as e:
            logger.warning(f"recall meta: {e}")
            return None
    try:
        return await ask_ai_async(
            prompt=("Ты вспоминаешь последнее медиа. Опиши коротко в стиле Кульша. Без markdown. "
                    "НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif."),
            image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id,
        )
    except Exception as e:
        logger.warning(f"recall image: {e}")
        return None

# ============================================================
# LOOKSMAXXING TIERS
# ============================================================
TIER_DISTRIBUTION = [
    {"key": "sub3",     "short": "S3",  "full_m": "SUB 3",     "full_f": "SUB 3",     "psl_low": 1.0, "psl_high": 2.4},
    {"key": "sub5",     "short": "S5",  "full_m": "SUB 5",     "full_f": "SUB 5",     "psl_low": 2.5, "psl_high": 3.9},
    {"key": "ltn",      "short": "LTN", "full_m": "LTN",       "full_f": "LTB",       "psl_low": 4.0, "psl_high": 5.5},
    {"key": "mtn",      "short": "MTN", "full_m": "MTN",       "full_f": "MTB",       "psl_low": 5.6, "psl_high": 6.3},
    {"key": "htn",      "short": "HTN", "full_m": "HTN",       "full_f": "HTB",       "psl_low": 6.4, "psl_high": 6.9},
    {"key": "chadlite", "short": "CL",  "full_m": "CHADLITE",  "full_f": "STACYLITE", "psl_low": 7.0, "psl_high": 7.4},
    {"key": "chad",     "short": "CH",  "full_m": "CHAD",      "full_f": "STACY",     "psl_low": 7.5, "psl_high": 7.6},
    {"key": "adamlite", "short": "AL",  "full_m": "ADAMLITE",  "full_f": "EVELITE",   "psl_low": 7.7, "psl_high": 7.8},
    {"key": "trueadam", "short": "TA",  "full_m": "TRUE ADAM", "full_f": "TRUE EVE",  "psl_low": 7.9, "psl_high": 8.0},
]


def find_tier_key(tier_name: str) -> str | None:
    if not tier_name:
        return None
    tn = tier_name.strip().upper().replace("_", " ").replace("-", " ")
    for t in TIER_DISTRIBUTION:
        candidates = [t["key"].upper(), t["short"].upper(), t["full_m"].upper(), t["full_f"].upper()]
        if tn in candidates or tn.replace(" ", "") in [c.replace(" ", "") for c in candidates]:
            return t["key"]
    return None


def get_tier_color(tier_key_or_name: str) -> str:
    key = find_tier_key(tier_key_or_name) or (tier_key_or_name or "").strip().lower()
    if key in ("sub3", "sub5"):
        return "#E53E3E"
    if key in ("ltn", "mtn"):
        return "#ECC94B"
    if key in ("htn", "chadlite", "chad", "adamlite"):
        return "#38A169"
    if key == "trueadam":
        return "#9F7AEA"
    return "#38A169"


def is_looksmaxxing_command(text: str) -> bool:
    t = (text or "").strip().lower()
    return bool(re.match(r'^(кульш\s+)?psl(\s+(совет|advice))?$', t))


def is_battle_command(text: str) -> bool:
    t = (text or "").strip().lower()
    return bool(re.match(r'^(кульш\s+)?(battle|баттл|батл)$', t))

# ============================================================
# INFOGRAPHIC
# ============================================================
def load_font(size: int):
    font_path = os.path.join("fonts", "Montserrat-Bold.ttf")
    try:
        return ImageFont.truetype(font_path, size)
    except IOError:
        return ImageFont.load_default()


def add_bullet(text: str) -> str:
    if text.startswith("•") or text.startswith("-"):
        return text
    return f"• {text}"


def _wrap_text(text, draw, font, max_width):
    words = text.split(' ')
    lines = []
    cur = ""
    for w in words:
        test = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _block_height(lines, font, line_spacing, draw):
    total = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total += bbox[3] - bbox[1] + line_spacing
    if total > 0:
        total -= line_spacing
    return total


async def create_infographic(photo_bytes: bytes, data: dict, theme: str = "dark", lang: str = "en") -> BytesIO:
    if lang == "ru":
        TITLE = "ОТЧЁТ LOOKSMAXXING"
        PSL_LABEL = "PSL"
        STRENGTHS = "ПРЕИМУЩЕСТВ."
        WEAKNESSES = "НЕДОСТАТКИ"
        FULL_ANALYSIS = "Полный анализ в сообщении"
        METRIC_NAMES = {"skin": "Кожа", "eyes": "Глаза", "jawline": "Челюсть", "bloat": "Одутловатость",
                        "hair": "Волосы", "bone_structure": "Костная структура", "symmetry": "Симметрия",
                        "canthal_tilt": "Кант. наклон"}
        BETTER_THAN = "Вы превосходите {}% людей"
        DISTRIBUTION_CAPTION = "Распределение тиров"
        POTENTIAL_LABEL = "Потенциал:"
    else:
        TITLE = "LOOKSMAXXING REPORT"
        PSL_LABEL = "PSL"
        STRENGTHS = "STRENGTHS"
        WEAKNESSES = "WEAKNESSES"
        FULL_ANALYSIS = "Full analysis in the message"
        METRIC_NAMES = {"skin": "Skin", "eyes": "Eyes", "jawline": "Jawline", "bloat": "Bloat",
                        "hair": "Hair", "bone_structure": "Bone structure", "symmetry": "Symmetry",
                        "canthal_tilt": "Canthal tilt"}
        BETTER_THAN = "You outperform {}% of people"
        DISTRIBUTION_CAPTION = "Tier distribution"
        POTENTIAL_LABEL = "Potential:"

    if theme == "light":
        bg_color = "#F9F9FB"
        text_primary = "#1A1A2E"
        text_secondary = "#4A4A6A"
        text_tertiary = "#6B6B80"
        accent = "#2B6CB0"
        line_color = "#D1D5DB"
        scale_bg = "#E5E7EB"
        weak_color = "#C53030"
        highlight_outline = "#1A1A2E"
    else:
        bg_color = "#0E0E12"
        text_primary = "#F3F4F6"
        text_secondary = "#9CA3AF"
        text_tertiary = "#6B6B80"
        accent = "#10B981"
        line_color = "#2A2A3A"
        scale_bg = "#2A2A3A"
        weak_color = "#E53E3E"
        highlight_outline = "#FFFFFF"

    canvas_w, canvas_h = 1000, 1000
    image = Image.new("RGBA", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(image)

    font_title = load_font(34)
    font_psl_num = load_font(56)
    font_sub = load_font(24)
    font_text = load_font(18)
    font_small = load_font(15)
    font_scale = load_font(16)
    list_font = load_font(17)
    font_tier_label = load_font(13)

    draw.text((40, 25), TITLE, fill=text_tertiary, font=font_title)
    draw.line([(40, 70), (canvas_w - 40, 70)], fill=line_color, width=1)

    user_img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
    user_img.thumbnail((430, 530), Image.Resampling.LANCZOS)
    mask = Image.new("L", user_img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0) + user_img.size, radius=28, fill=255)
    rounded = Image.new("RGBA", user_img.size, (0, 0, 0, 0))
    rounded.paste(user_img, (0, 0), mask=mask)
    photo_x, photo_y = 40, 100
    image.paste(rounded, (photo_x, photo_y), rounded)

    psl_score = data.get("psl", "N/A")
    tier_name = str(data.get("tier", "N/A")).upper()
    gender = data.get("gender", "N/A")
    potential = data.get("potential", "N/A")
    try:
        psl_val = max(1.0, min(8.0, float(psl_score)))
    except (ValueError, TypeError):
        psl_val = 1.0
    current_tier_idx = -1
    fk = find_tier_key(tier_name)
    if fk:
        for idx, t in enumerate(TIER_DISTRIBUTION):
            if t["key"] == fk:
                current_tier_idx = idx
                break
    if current_tier_idx == -1:
        for idx, t in enumerate(TIER_DISTRIBUTION):
            if t["psl_low"] <= psl_val <= t["psl_high"]:
                current_tier_idx = idx
                break
    if current_tier_idx == -1:
        current_tier_idx = 4

    better_than = max(0.1, min(99.9, (psl_val - 1) / 7 * 100))
    better_text = BETTER_THAN.format(round(better_than, 1))
    photo_bottom = photo_y + rounded.size[1]
    draw.text((40, photo_bottom + 20), better_text, fill=text_secondary, font=font_sub)

    chart_x = 40
    chart_y = photo_bottom + 65
    chart_width = 430
    chart_height = 20
    total_range = 8.0 - 1.0
    for tier in TIER_DISTRIBUTION:
        low, high = tier["psl_low"], tier["psl_high"]
        x_start = chart_x + (low - 1.0) / total_range * chart_width
        x_end = chart_x + (high - 1.0) / total_range * chart_width
        draw.rectangle([x_start, chart_y, x_end, chart_y + chart_height], fill=get_tier_color(tier["key"]))
        if tier["key"] == TIER_DISTRIBUTION[current_tier_idx]["key"]:
            draw.rectangle([x_start - 1, chart_y - 1, x_end + 1, chart_y + chart_height + 1],
                           outline=highlight_outline, width=2)
        tb = draw.textbbox((0, 0), tier["short"], font=font_tier_label)
        tw = tb[2] - tb[0]
        draw.text(((x_start + x_end) / 2 - tw / 2, chart_y + chart_height + 4),
                  tier["short"], fill=text_secondary, font=font_tier_label)
    draw.text((40, chart_y + chart_height + 30), DISTRIBUTION_CAPTION, fill=text_tertiary, font=font_small)

    start_x = 510
    right_top_y = 100
    draw.text((start_x, right_top_y), PSL_LABEL, fill=text_tertiary, font=font_sub)
    draw.text((start_x, right_top_y + 35), f"{psl_score}", fill=text_primary, font=font_psl_num)
    draw.text((start_x, right_top_y + 110), f"{tier_name} · {gender}", fill=accent, font=font_sub)
    draw.text((start_x, right_top_y + 145), f"{POTENTIAL_LABEL} {potential}", fill=text_secondary, font=font_small)

    psl_bar_x, psl_bar_y = start_x, right_top_y + 200
    psl_bar_w, psl_bar_h = 400, 20
    draw.rounded_rectangle((psl_bar_x, psl_bar_y, psl_bar_x + psl_bar_w, psl_bar_y + psl_bar_h),
                           radius=10, fill=scale_bg)
    fw = int((psl_val - 1) / 7 * psl_bar_w)
    if fw > 0:
        draw.rounded_rectangle((psl_bar_x, psl_bar_y, psl_bar_x + fw, psl_bar_y + psl_bar_h),
                               radius=10, fill=get_tier_color(tier_name))
    for i in range(1, 9):
        x = psl_bar_x + (i - 1) / 7 * psl_bar_w
        draw.line([(x, psl_bar_y - 6), (x, psl_bar_y)], fill=text_tertiary, width=1)
        bbox = draw.textbbox((0, 0), str(i), font=font_scale)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw / 2, psl_bar_y - 24), str(i), fill=text_secondary, font=font_scale)

    metrics_mapping = [
        ("skin", data.get("skin", "N/A")), ("eyes", data.get("eyes", "N/A")),
        ("jawline", data.get("jawline", "N/A")), ("bloat", data.get("bloat", "N/A")),
        ("hair", data.get("hair", "N/A")), ("bone_structure", data.get("bone_structure", "N/A")),
        ("symmetry", data.get("symmetry", "N/A")), ("canthal_tilt", data.get("canthal_tilt", "N/A")),
    ]
    right_margin = start_x + 430
    col1_x = start_x
    col1_width = 200
    col2_x = col1_x + col1_width + 20
    col2_width = right_margin - col2_x
    base_row_height = 38
    min_padding = 6
    line_spacing = 2
    current_y = psl_bar_y + psl_bar_h + 25
    for key, val_str in metrics_mapping:
        title = METRIC_NAMES.get(key, key)
        tb = draw.textbbox((0, 0), title, font=font_text)
        title_h = tb[3] - tb[1]
        val_lines = _wrap_text(str(val_str), draw, font_text, col2_width)
        val_block_h = _block_height(val_lines, font_text, line_spacing, draw)
        row_height = max(base_row_height, title_h + 2 * min_padding, val_block_h + 2 * min_padding)
        draw.line([(col1_x, current_y), (right_margin, current_y)], fill=line_color, width=1)
        draw.text((col1_x, current_y + (row_height - title_h) / 2), title, fill=text_secondary, font=font_text)
        val_y = current_y + (row_height - val_block_h) / 2
        for line in val_lines:
            bbox = draw.textbbox((0, 0), line, font=font_text)
            lh = bbox[3] - bbox[1]
            draw.text((col2_x, val_y), line, fill=text_primary, font=font_text)
            val_y += lh + line_spacing
        current_y += row_height
    draw.line([(col1_x, current_y), (right_margin, current_y)], fill=line_color, width=1)

    pros = data.get("pros", [])
    cons = data.get("cons", [])
    if isinstance(pros, str):
        pros = [pros]
    if isinstance(cons, str):
        cons = [cons]
    pros = [add_bullet(p) for p in pros]
    cons = [add_bullet(c) for c in cons]
    col_y = current_y + 20
    draw.text((start_x, col_y), STRENGTHS, fill=accent, font=font_sub)
    draw.text((start_x + 220, col_y), WEAKNESSES, fill=weak_color, font=font_sub)
    col_width = 200
    line_height = 26
    list_start_y = col_y + 38

    def render_list(items, x, y, color, max_width=col_width):
        cy = y
        for item in items:
            for line in _wrap_text(item, draw, list_font, max_width):
                draw.text((x, cy), line, fill=color, font=list_font)
                cy += line_height
            cy += 4
        return cy

    end_left = render_list(pros, start_x + 10, list_start_y, text_primary)
    end_right = render_list(cons, start_x + 230, list_start_y, text_primary)
    max_y = max(end_left, end_right)
    draw.text((40, max_y + 30), FULL_ANALYSIS, fill=text_tertiary, font=font_small)
    out = BytesIO()
    image.save(out, format="PNG")
    out.seek(0)
    return out


async def create_battle_infographic(p1: bytes, p2: bytes, data: dict, theme="dark", lang="en") -> BytesIO:
    if lang == "ru":
        TITLE = "БАТТЛ LOOKSMAXXING"
        FACTOR_LABELS = {"skin": "Кожа", "eyes": "Глаза", "jawline": "Челюсть", "bloat": "Одутловатость",
                         "hair": "Волосы", "bone_structure": "Костная структура", "symmetry": "Симметрия",
                         "canthal_tilt": "Кант. наклон"}
        MOGGED_TEXT = "МОГГНУТ"
        WINNER_LABEL = "ПОБЕДИТЕЛЬ"
    else:
        TITLE = "LOOKSMAXXING BATTLE"
        FACTOR_LABELS = {"skin": "Skin", "eyes": "Eyes", "jawline": "Jawline", "bloat": "Bloat",
                         "hair": "Hair", "bone_structure": "Bone structure", "symmetry": "Symmetry",
                         "canthal_tilt": "Canthal tilt"}
        MOGGED_TEXT = "MOGGED"
        WINNER_LABEL = "WINNER"

    if theme == "light":
        bg_color = "#F9F9FB"
        text_primary = "#1A1A2E"
        text_secondary = "#4A4A6A"
        text_tertiary = "#6B6B80"
        accent = "#2B6CB0"
        line_color = "#D1D5DB"
        scale_bg = "#E5E7EB"
        mogged_color = (0, 0, 0, 180)
        mogged_text_color = "#E53E3E"
    else:
        bg_color = "#0E0E12"
        text_primary = "#F3F4F6"
        text_secondary = "#9CA3AF"
        text_tertiary = "#6B6B80"
        accent = "#10B981"
        line_color = "#2A2A3A"
        scale_bg = "#2A2A3A"
        mogged_color = (0, 0, 0, 180)
        mogged_text_color = "#E53E3E"

    canvas_w, canvas_h = 1300, 1300
    image = Image.new("RGBA", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(image)
    font_title = load_font(34)
    font_psl_num = load_font(56)
    font_sub = load_font(24)
    font_text = load_font(18)
    font_scale = load_font(16)
    font_winner = load_font(30)
    font_mogged = load_font(48)

    draw.text((canvas_w // 2, 25), TITLE, fill=text_tertiary, font=font_title, anchor="mm")
    draw.line([(40, 70), (canvas_w - 40, 70)], fill=line_color, width=1)

    col_width = 550
    left_x = 50
    right_x = canvas_w - 50 - col_width
    photo_y = 110
    photo_width = col_width
    photo_height = 500

    def paste_rounded(img_bytes, x, y, w, h, radius=28):
        im = Image.open(BytesIO(img_bytes)).convert("RGBA")
        im.thumbnail((w, h), Image.Resampling.LANCZOS)
        ix = x + (w - im.width) // 2
        iy = y + (h - im.height) // 2
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0) + im.size, radius=radius, fill=255)
        rounded = Image.new("RGBA", im.size, (0, 0, 0, 0))
        rounded.paste(im, (0, 0), mask=mask)
        image.paste(rounded, (ix, iy), rounded)
        return ix, iy, im.width, im.height

    left_rect = paste_rounded(p1, left_x, photo_y, photo_width, photo_height)
    right_rect = paste_rounded(p2, right_x, photo_y, photo_width, photo_height)

    winner_num = str(data.get("winner", "1"))
    loser_num = "2" if winner_num == "1" else "1"
    loser_rect = left_rect if loser_num == "1" else right_rect
    strip_height = 80
    strip_y = loser_rect[1] + (loser_rect[3] - strip_height) // 2
    overlay = Image.new("RGBA", (loser_rect[2], strip_height), mogged_color)
    image.paste(overlay, (loser_rect[0], strip_y), overlay)
    draw.text((loser_rect[0] + loser_rect[2] // 2, strip_y + strip_height // 2),
              MOGGED_TEXT, fill=mogged_text_color, font=font_mogged, anchor="mm")

    winner_rect = left_rect if winner_num == "1" else right_rect
    winner_y = photo_y + photo_height + 30
    draw.text((winner_rect[0] + winner_rect[2] // 2, winner_y),
              WINNER_LABEL, fill=accent, font=font_winner, anchor="mm")

    info_y = winner_y + 70
    for side, rect, key in [(1, left_rect, "photo1"), (2, right_rect, "photo2")]:
        pd = data.get(key, {})
        psl = pd.get("psl", "N/A")
        tier = pd.get("tier", "N/A")
        gender = pd.get("gender", "N/A")
        factors = pd.get("factors", {})
        if side == 1:
            anchor = "ls"
            bar_x = rect[0]
        else:
            anchor = "rs"
            bar_x = rect[0] + rect[2]
        draw.text((bar_x, info_y), f"PSL: {psl}", fill=text_primary, font=font_psl_num, anchor=anchor)
        draw.text((bar_x, info_y + 50), f"{tier} · {gender}", fill=accent, font=font_sub, anchor=anchor)
        try:
            psl_val = float(psl)
        except (ValueError, TypeError):
            psl_val = 1.0
        psl_val = max(1.0, min(8.0, psl_val))
        bar_w = rect[2]
        bar_y = info_y + 95
        bar_h = 20
        if side == 1:
            draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=10, fill=scale_bg)
            fw = int((psl_val - 1) / 7 * bar_w)
            if fw > 0:
                draw.rounded_rectangle((bar_x, bar_y, bar_x + fw, bar_y + bar_h),
                                       radius=10, fill=get_tier_color(tier))
            for i in range(1, 9):
                x = bar_x + (i - 1) / 7 * bar_w
                draw.line([(x, bar_y - 6), (x, bar_y)], fill=text_tertiary, width=1)
                bbox = draw.textbbox((0, 0), str(i), font=font_scale)
                tw = bbox[2] - bbox[0]
                draw.text((x - tw / 2, bar_y - 24), str(i), fill=text_secondary, font=font_scale)
        else:
            draw.rounded_rectangle((bar_x - bar_w, bar_y, bar_x, bar_y + bar_h), radius=10, fill=scale_bg)
            fw = int((psl_val - 1) / 7 * bar_w)
            if fw > 0:
                draw.rounded_rectangle((bar_x - fw, bar_y, bar_x, bar_y + bar_h),
                                       radius=10, fill=get_tier_color(tier))
            for i in range(1, 9):
                x = bar_x - (i - 1) / 7 * bar_w
                draw.line([(x, bar_y - 6), (x, bar_y)], fill=text_tertiary, width=1)
                bbox = draw.textbbox((0, 0), str(i), font=font_scale)
                tw = bbox[2] - bbox[0]
                draw.text((x - tw / 2, bar_y - 24), str(i), fill=text_secondary, font=font_scale)
        fy = bar_y + bar_h + 25
        for idx, (fk, label) in enumerate(FACTOR_LABELS.items()):
            if fk in factors:
                val = factors[fk]
                if isinstance(val, (int, float)):
                    val = str(val)
                draw.text((bar_x, fy + idx * 28), f"{label}: {val}",
                          fill=text_secondary, font=font_text, anchor=anchor)
    out = BytesIO()
    image.save(out, format="PNG")
    out.seek(0)
    return out

# ============================================================
# LOOKSMAXXING AI DATA
# ============================================================
TIER_RULES_M = "SUB 3, SUB 5, LTN, MTN, HTN, CHADLITE, CHAD, ADAMLITE, TRUE ADAM"
TIER_RULES_F = "SUB 3, SUB 5, LTB, MTB, HTB, STACYLITE, STACY, EVELITE, TRUE EVE"
TIER_RULES_STRICT = (
    f"Мужские тиры (СТРОГО): {TIER_RULES_M}.\n"
    f"Женские тиры (СТРОГО): {TIER_RULES_F}.\n"
    "ИСПОЛЬЗУЙ ТОЛЬКО ЭТИ НАЗВАНИЯ. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать 'High Normie', 'Low Tier Normie', "
    "'Subhuman', 'Sub-five', 'Sub-5 (Canine)', 'Animal' и любые другие выдуманные варианты. "
    "Если на фото не человек — верни tier 'N/A' и gender 'N/A'."
)


async def get_looksmaxxing_data(photo_bytes: bytes, include_advice: bool, lang: str = "en") -> dict[str, Any]:
    if lang == "ru":
        prompt = (
            "Ты — чрезвычайно строгий AI-аналитик по looksmaxxing. Оцени лицо критически. "
            "Определи пол, кожу, волосы, костную структуру, челюсть, глаза, одутловатость, симметрию, кантальный наклон. "
            "Кратко, пару слов в каждом поле JSON. Рассчитай PSL от 1.0 до 8.0.\n\n"
            f"{TIER_RULES_STRICT}\n\n"
            "Диапазоны PSL: SUB 3: 1.0–2.4; SUB 5: 2.5–3.9; LTN/LTB: 4.0–5.5; MTN/MTB: 5.6–6.3; HTN/HTB: 6.4–6.9; "
            "CHADLITE/STACYLITE: 7.0–7.4; CHAD/STACY: 7.5–7.6; ADAMLITE/EVELITE: 7.7–7.8; TRUE ADAM/TRUE EVE: 7.9–8.0.\n\n"
            "Также оцени потенциал (максимально возможный тир). "
            "Верни ТОЛЬКО валидный JSON без markdown. Поля: "
            '"gender", "psl", "tier", "potential", "skin", "eyes", "jawline", "bloat", "hair", "bone_structure", '
            '"symmetry", "canthal_tilt", "pros" (массив 2-3), "cons" (массив 2-3), "summary"'
            + (', "advice" (советы).' if include_advice else ', "advice": ""')
        )
    else:
        prompt = (
            "You are an extremely strict and objective AI looksmaxxing analyst. Evaluate the face critically. "
            "Determine gender, skin, hair, bone structure, jawline, eyes, bloat, symmetry, canthal tilt. Brief fields. "
            "PSL 1.0-8.0.\n\n"
            f"{TIER_RULES_STRICT}\n\n"
            "PSL ranges: SUB 3: 1.0–2.4; SUB 5: 2.5–3.9; LTN/LTB: 4.0–5.5; MTN/MTB: 5.6–6.3; HTN/HTB: 6.4–6.9; "
            "CHADLITE/STACYLITE: 7.0–7.4; CHAD/STACY: 7.5–7.6; ADAMLITE/EVELITE: 7.7–7.8; TRUE ADAM/TRUE EVE: 7.9–8.0.\n\n"
            "Return ONLY valid JSON, no markdown. Fields: "
            '"gender", "psl", "tier", "potential", "skin", "eyes", "jawline", "bloat", "hair", "bone_structure", '
            '"symmetry", "canthal_tilt", "pros" (array 2-3), "cons" (array 2-3), "summary"'
            + (', "advice" (tips).' if include_advice else ', "advice": ""')
        )
    raw = await ask_ai_async(
        prompt=prompt, image_bytes=photo_bytes, image_mime="image/jpeg",
        system_instruction_override=(
            "You are a professional looksmaxxing AI. Answer ONLY with JSON. "
            "STRICT tier names only, no synonyms, no invented variants."
        ),
    )
    try:
        return cast(dict, json.loads(clean_json_text(raw)))
    except json.JSONDecodeError:
        logger.error(f"Looksmaxxing JSON decode: {raw[:200]}")
        return {"error": "Не удалось распарсить ответ ИИ."}


async def get_battle_data(p1: bytes, p2: bytes, lang: str = "en") -> dict[str, Any]:
    if lang == "ru":
        prompt = (
            "Ты — строгий AI-аналитик looksmaxxing. Сравни два лица, выбери победителя по PSL.\n\n"
            f"{TIER_RULES_STRICT}\n\n"
            "Верни JSON: photo1 {psl, tier, gender, factors {skin, eyes, jawline, bloat, hair, bone_structure, "
            "symmetry, canthal_tilt} (0-8), summary}, photo2 {...}, winner (\"1\" или \"2\"), reason. Без markdown. "
            "Только указанные названия тиров."
        )
    else:
        prompt = (
            "You are a strict looksmaxxing AI. Compare two faces, choose winner by PSL.\n\n"
            f"{TIER_RULES_STRICT}\n\n"
            "Return JSON: photo1 {psl, tier, gender, factors {skin, eyes, jawline, bloat, hair, bone_structure, "
            "symmetry, canthal_tilt} (0-8), summary}, photo2 {...}, winner (\"1\" or \"2\"), reason. No markdown. "
            "Only exact tier names. Do NOT invent new ones."
        )
    raw = await ask_ai_async(
        prompt=prompt,
        system_instruction_override=(
            "You are a looksmaxxing AI that outputs only JSON. STRICT tier names only: "
            f"male = {TIER_RULES_M}; female = {TIER_RULES_F}. "
            "Never use 'High Normie', 'Low Tier Normie', 'Subhuman', 'Animal', etc."
        ),
        image_bytes_list=[p1, p2], image_mime_list=["image/jpeg", "image/jpeg"],
    )
    try:
        return cast(dict, json.loads(clean_json_text(raw)))
    except json.JSONDecodeError:
        logger.error(f"Battle JSON decode: {raw[:200]}")
        return {"error": "Could not parse AI response as JSON."}

# ============================================================
# STYLED BUTTON (Bot API 10.3 — цвета: primary/success/danger)
# ============================================================
class StyledButton(InlineKeyboardButton):
    def __init__(self, text: str, style: str | None = None, **kwargs):
        super().__init__(text, **kwargs)
        self.style = style

    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.style:
            d['style'] = self.style
        return d


def btn(text: str, style: str | None = None, **kwargs) -> StyledButton:
    return StyledButton(text, style=style, **kwargs)

# ============================================================
# CONFIG TEXT / KEYBOARDS
# ============================================================
def _localize(lang: str, ru: str, en: str) -> str:
    return ru if lang == "ru" else en


def _config_text(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    prompt_safe = html.escape(cfg.get("custom_prompt") or _localize(lang, "стандартный", "default"))
    title = _localize(lang, "Настройки", "Settings")
    line = "━━━━━━━━━━━━━━━━━━━━"
    lang_label = _localize(lang, "Язык", "Language")
    theme_label = _localize(lang, "Тема", "Theme")
    model_label = _localize(lang, "Модель", "Model")
    temp_label = _localize(lang, "Температура", "Temperature")
    sep_label = _localize(lang, "Разбивка", "Split")
    stream_label = _localize(lang, "Стриминг", "Streaming")
    stickers_label = _localize(lang, "Стикеры/гифки", "Stickers/GIFs")
    autoreply_label = _localize(lang, "Автоответ", "Auto-reply")
    random_label = _localize(lang, "Случайные", "Random")
    prompt_label = _localize(lang, "Кастомный промпт", "Custom prompt")
    credits_label = _localize(lang, "Кредиты", "Credits")
    on = "✅"
    off = "❌"
    theme_disp = _localize(lang, "тёмная", "dark") if cfg.get("theme", "dark") == "dark" else _localize(lang, "светлая", "light")
    credits = get_user_credits(platform, user_id)
    stream_txt = f"{on if cfg.get('streaming_enabled') else off} · {'premium' if premium_functions_enabled else 'off'}"
    return (
        f"{title}\n{line}\n"
        f"🌐 {lang_label}: {'Русский 🇷🇺' if lang == 'ru' else 'English 🇬🇧'}\n"
        f"🌓 {theme_label}: {theme_disp}\n"
        f"🧠 {model_label}: {model_display_name(cfg.get('model'))}\n"
        f"🎛 {temp_label}: <code>{cfg.get('temperature', 0.9)}</code>\n"
        f"💬 {sep_label}: {on if cfg.get('separate_enabled', True) else off}\n"
        f"📡 {stream_label}: {stream_txt}\n"
        f"🎨 {stickers_label}: {on if cfg.get('stickers_enabled', True) else off}\n"
        f"🗣 {autoreply_label}: {on if cfg.get('random_reply_enabled') else off}\n"
        f"📢 {random_label}: {on if cfg.get('random_messages_enabled', True) else off}\n"
        f"💎 {credits_label}: <code>{credits}/{DAILY_CREDITS}</code>\n"
        f"{line}\n"
        f"📝 {prompt_label}: {prompt_safe}"
    )


def build_main_config_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn(_localize(lang, "🌐 Язык", "🌐 Language"), style=None, callback_data="cfg:lang"),
        btn(_localize(lang, "🌓 Тема", "🌓 Theme"), style=None, callback_data="cfg:theme"),
    )
    kb.row(
        btn(f"🧠 {_localize(lang, 'Модель', 'Model')}: {model_display_name(cfg.get('model'))}",
            style="primary", callback_data="cfg:model"),
        btn(f"🎛 {_localize(lang, 'Темп.', 'Temp')}: {cfg.get('temperature', 0.9)}",
            style=None, callback_data="cfg:temp"),
    )
    kb.row(
        btn(f"💬 {_localize(lang, 'Разбивка', 'Split')}: {'✅' if cfg.get('separate_enabled', True) else '❌'}",
            style=None, callback_data="cfg:separate"),
        btn(f"📡 {_localize(lang, 'Стриминг', 'Streaming')}: {'✅' if cfg.get('streaming_enabled') else '❌'}",
            style=None, callback_data="cfg:streaming"),
    )
    kb.row(
        btn(f"🎨 {_localize(lang, 'Стикеры', 'Stickers')}: {'✅' if cfg.get('stickers_enabled', True) else '❌'}",
            style=None, callback_data="cfg:stickers"),
        btn(f"🗣 {_localize(lang, 'Автоотв.', 'Auto-reply')}: {'✅' if cfg.get('random_reply_enabled') else '❌'}",
            style=None, callback_data="cfg:autoreply"),
    )
    kb.row(
        btn(f"📢 {_localize(lang, 'Рандом', 'Random')}: {'✅' if cfg.get('random_messages_enabled', True) else '❌'}",
            style=None, callback_data="cfg:random"),
    )
    kb.row(
        btn("📝 " + _localize(lang, "Изменить промпт", "Edit prompt"),
            style="primary", callback_data="cfg:prompt"),
    )
    kb.row(
        btn("🧹 " + _localize(lang, "Сбросить память", "Reset memory"),
            style="danger", callback_data="cfg:reset_memory"),
        btn("♻️ " + _localize(lang, "Сбросить промпт", "Reset prompt"),
            style="danger", callback_data="cfg:reset_prompt"),
    )
    kb.row(
        btn("✅ " + _localize(lang, "Применить и закрыть", "Apply & close"),
            style="success", callback_data="cfg:apply")
    )
    return kb


def build_model_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    cur = cfg.get("model")
    kb = InlineKeyboardMarkup()
    auto_mark = "🔘" if not cur else "▫️"
    kb.row(btn(f"{auto_mark} 🎲 {_localize(lang, 'Авто', 'Auto')}", style=None, callback_data="cfg:model_set:auto"))
    row: list[StyledButton] = []
    for idx, model in enumerate(MODEL_LIST):
        mark = "🔘" if cur == model else "▫️"
        row.append(btn(f"{mark} {MODEL_DISPLAY.get(model, model)}", style=None, callback_data=f"cfg:model_set:{idx}"))
        if len(row) == 2:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    kb.row(btn("🔙 " + _localize(lang, "Назад", "Back"), style="primary", callback_data="cfg:model_back"))
    return kb


def build_lang_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    cur = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn(f"{'🔘' if cur == 'ru' else '▫️'} Русский 🇷🇺",
            style="primary" if cur == "ru" else None, callback_data="cfg:lang_set:ru"),
        btn(f"{'🔘' if cur == 'en' else '▫️'} English 🇬🇧",
            style="primary" if cur == "en" else None, callback_data="cfg:lang_set:en"),
    )
    kb.row(btn("🔙 Назад / Back", style="primary", callback_data="cfg:sub_back"))
    return kb


def build_theme_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    cur = cfg.get("theme", "dark")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn(f"{'🔘' if cur == 'dark' else '▫️'} Тёмная 🌑",
            style="primary" if cur == "dark" else None, callback_data="cfg:theme_set:dark"),
        btn(f"{'🔘' if cur == 'light' else '▫️'} Светлая ☀️",
            style="primary" if cur == "light" else None, callback_data="cfg:theme_set:light"),
    )
    kb.row(btn("🔙 Назад / Back", style="primary", callback_data="cfg:sub_back"))
    return kb


def build_temp_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    cur = cfg.get("temperature", 0.9)
    kb = InlineKeyboardMarkup()
    values = [0.2, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
    row: list[StyledButton] = []
    for v in values:
        mark = "🔘" if abs(cur - v) < 0.01 else "▫️"
        row.append(btn(f"{mark} {v}", style=None, callback_data=f"cfg:temp_set:{v}"))
    kb.row(*row[:4])
    kb.row(*row[4:])
    kb.row(btn("🔙 Назад / Back", style="primary", callback_data="cfg:sub_back"))
    return kb


def _model_picker_text(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    cur = cfg.get("model")
    return (
        f"🧠 <b>{_localize(lang, 'Выбор модели', 'Model selection')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{_localize(lang, 'Текущая', 'Current')}: {model_display_name(cur)}\n\n"
        f"🎲 <b>{_localize(lang, 'Авто', 'Auto')}</b> — {_localize(lang, 'перебор всех моделей', 'bot tries all models')}"
    )

# ============================================================
# МЕНЮ / START / HELP / DONATE — нейтральные тексты
# ============================================================
def _build_menu_text(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    if lang == "ru":
        return (
            "|K|*U*|L|*S*|H|\n\n"
            "# Кульш AI — главное меню\n\n"
            "Открытая языковая модель с набором встроенных инструментов. "
            "Ниже — основные разделы и команды для работы с ботом.\n\n"
            "**Что доступно:**\n"
            "- **Mini App** — расширенный чат с ИИ внутри Telegram\n"
            "- **Настройки** — язык, тема, модель, промпт, автоответы\n"
            "- **Команды** — полный список возможностей\n"
            "- **Донат** — поддержка разработки\n"
            "- **GitHub** — исходный код проекта\n"
        )
    return (
        "|K|*U*|L|*S*|H|\n\n"
        "# Kulsh AI — main menu\n\n"
        "An open-source language model with a set of built-in tools. "
        "Below are the main sections and commands for working with the bot.\n\n"
        "**Available:**\n"
        "- **Mini App** — extended AI chat inside Telegram\n"
        "- **Settings** — language, theme, model, prompt, auto-replies\n"
        "- **Commands** — full feature list\n"
        "- **Donate** — support development\n"
        "- **GitHub** — project source code\n"
    )


def _build_start_text(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    if lang == "ru":
        return (
            "# Кульш на связи\n\n"
            "Открытая языковая модель с возможностями анализа изображений, "
            "оценки внешности и настройки под себя. Работает в Telegram и Discord.\n\n"
            "**С чего начать:**\n"
            "- **Mini App** — расширенный чат с ИИ\n"
            "- **Меню** — все разделы и настройки\n"
            "- `кульш конфиг` — тонкая настройка под тебя\n\n"
            f"Веб-версия: {MINI_APP_URL}"
        )
    return (
        "# Kulsh is online\n\n"
        "An open-source language model with image analysis, looksmaxxing, "
        "and personal configuration. Available in Telegram and Discord.\n\n"
        "**Get started:**\n"
        "- **Mini App** — extended AI chat\n"
        "- **Menu** — all sections and settings\n"
        "- `kulsh config` — tune the bot\n\n"
        f"Web version: {MINI_APP_URL}"
    )


def build_menu_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn("🚀 " + _localize(lang, "Открыть Mini App", "Open Mini App"),
            style="primary", web_app=WebAppInfo(url=MINI_APP_URL))
    )
    kb.row(
        btn("⚙️ " + _localize(lang, "Настройки", "Settings"),
            style="success", callback_data="menu:settings"),
        btn("📖 " + _localize(lang, "Команды", "Commands"),
            style=None, callback_data="menu:help"),
    )
    kb.row(
        btn("💎 " + _localize(lang, "Донат", "Donate"),
            style=None, url=DONATE_URL),
        btn("🔗 " + _localize(lang, "GitHub", "GitHub"),
            style=None, url=GITHUB_URL),
    )
    kb.row(
        btn("❌ " + _localize(lang, "Закрыть", "Close"),
            style="danger", callback_data="menu:close")
    )
    return kb


def build_start_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn("🚀 " + _localize(lang, "Открыть Mini App", "Open Mini App"),
            style="primary", web_app=WebAppInfo(url=MINI_APP_URL))
    )
    kb.row(
        btn("📖 " + _localize(lang, "Меню", "Menu"),
            style="success", callback_data="menu:open"),
        btn("⚙️ " + _localize(lang, "Настройки", "Settings"),
            style=None, callback_data="menu:settings"),
    )
    kb.row(
        btn("💎 " + _localize(lang, "Донат", "Donate"),
            style=None, url=DONATE_URL),
        btn("🔗 " + _localize(lang, "GitHub", "GitHub"),
            style=None, url=GITHUB_URL),
    )
    return kb

# ============================================================
# CALLBACK HANDLER (cfg:)
# ============================================================
async def _edit_or_send(call: telebot.types.CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    try:
        await tg_bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=kb,
        )
    except Exception as e:
        logger.warning(f"edit_message_text fail: {e}")


MUTEX_SEP_STREAM_RU = "«Разбивка» и «Стриминг» взаимно исключаемы. Сначала отключите вторую настройку."
MUTEX_SEP_STREAM_EN = "«Split» and «Streaming» are mutually exclusive. Disable the other first."


@tg_bot.callback_query_handler(func=lambda call: call.data.startswith("cfg:"))
async def handle_cfg_callback(call: telebot.types.CallbackQuery) -> None:
    owner = config_msg_owners.get(call.message.message_id)
    if owner is not None and owner != call.from_user.id:
        await tg_bot.answer_callback_query(call.id, "это не твои настройки", show_alert=False)
        return

    chat_id = call.message.chat.id
    user_id = call.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    parts = call.data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    toast = _localize(lang, "Обновлено", "Updated")

    if action == "model_set":
        value = parts[2] if len(parts) > 2 else "auto"
        if value == "auto":
            cfg["model"] = None
            toast = _localize(lang, "Модель: авто", "Model: auto")
        else:
            try:
                idx = int(value)
                if 0 <= idx < len(MODEL_LIST):
                    cfg["model"] = MODEL_LIST[idx]
                    toast = f"Модель: {MODEL_DISPLAY.get(MODEL_LIST[idx], MODEL_LIST[idx])}"
            except ValueError:
                pass
        await _edit_or_send(call, _model_picker_text("tg", chat_id, user_id),
                            build_model_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id, toast)
        return

    if action == "model":
        await _edit_or_send(call, _model_picker_text("tg", chat_id, user_id),
                            build_model_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id)
        return

    if action in ("model_back", "sub_back"):
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "lang":
        await _edit_or_send(call, "🌐 <b>Язык / Language</b>", build_lang_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "lang_set":
        val = parts[2] if len(parts) > 2 else "ru"
        if val in ("ru", "en"):
            cfg["language"] = val
            toast = "Язык: русский 🇷🇺" if val == "ru" else "Language: English 🇬🇧"
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id, toast)
        return

    if action == "theme":
        await _edit_or_send(call, "🌓 <b>Тема / Theme</b>", build_theme_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "theme_set":
        val = parts[2] if len(parts) > 2 else "dark"
        if val in ("dark", "light"):
            cfg["theme"] = val
            toast = "Тема: тёмная 🌑" if val == "dark" else "Тема: светлая ☀️"
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id, toast)
        return

    if action == "temp":
        await _edit_or_send(call, "🎛 <b>Температура / Temperature</b>", build_temp_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "temp_set":
        try:
            val = max(0.0, min(2.0, float(parts[2])))
            cfg["temperature"] = val
            toast = f"Температура: {val}"
        except (ValueError, IndexError):
            pass
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(call.id, toast)
        return

    if action == "prompt":
        # Запрашиваем промпт через ForceReply
        prompt_waiting[user_id] = call.message.message_id
        try:
            ask_text = _localize(
                lang,
                "Отправьте новый кастомный промпт одним сообщением (ответом на это). "
                "Чтобы отменить — ответьте `отмена`.",
                "Send the new custom prompt as a single reply to this message. "
                "To cancel — reply `cancel`.",
            )
            await tg_bot.send_message(
                chat_id, ask_text,
                parse_mode='HTML',
                reply_markup=ForceReply(selective=True),
            )
        except Exception as e:
            logger.warning(f"prompt ask fail: {e}")
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "apply":
        config_msg_owners.pop(call.message.message_id, None)
        chat_key = get_chat_key("tg", chat_id)
        trig_id = config_trigger_msgs.pop(chat_key, None)
        if trig_id:
            try:
                await tg_bot.delete_message(chat_id, trig_id)
            except Exception:
                pass
        await tg_bot.answer_callback_query(call.id, _localize(lang, "Готово", "Done"))
        asyncio.create_task(play_apply_animation(chat_id, call.message.message_id))
        return

    if action == "separate":
        new_val = not cfg.get("separate_enabled", True)
        if new_val and cfg.get("streaming_enabled", False):
            mutex_text = MUTEX_SEP_STREAM_RU if lang == "ru" else MUTEX_SEP_STREAM_EN
            await tg_bot.answer_callback_query(call.id, mutex_text, show_alert=False)
            return
        cfg["separate_enabled"] = new_val
    elif action == "streaming":
        if not premium_functions_enabled:
            await tg_bot.answer_callback_query(call.id, "расширенные функции отключены", show_alert=False)
            return
        new_val = not cfg.get("streaming_enabled", False)
        if new_val and cfg.get("separate_enabled", True):
            mutex_text = MUTEX_SEP_STREAM_RU if lang == "ru" else MUTEX_SEP_STREAM_EN
            await tg_bot.answer_callback_query(call.id, mutex_text, show_alert=False)
            return
        cfg["streaming_enabled"] = new_val
    elif action == "stickers":
        cfg["stickers_enabled"] = not cfg.get("stickers_enabled", True)
    elif action == "autoreply":
        cfg["random_reply_enabled"] = not cfg.get("random_reply_enabled", False)
    elif action == "random":
        cfg["random_messages_enabled"] = not cfg.get("random_messages_enabled", True)
    elif action == "reset_prompt":
        cfg["custom_prompt"] = None
        toast = _localize(lang, "Промпт сброшен", "Prompt reset")
    elif action == "reset_memory":
        chat_key = f"tg_{chat_id}"
        if chat_key in long_term_memory:
            del long_term_memory[chat_key]
            save_long_term_memory(long_term_memory)
        chat_memories[chat_key] = deque(maxlen=20)
        chat_media_history[chat_key].clear()
        last_random_reply.pop(chat_key, None)
        last_old_reply.pop(chat_key, None)
        toast = _localize(lang, "Память сброшена", "Memory reset")

    await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                        build_main_config_keyboard("tg", chat_id, user_id))
    await tg_bot.answer_callback_query(call.id, toast)

# ============================================================
# CALLBACK HANDLER (menu:)
# ============================================================
@tg_bot.callback_query_handler(func=lambda call: call.data.startswith("menu:"))
async def handle_menu_callback(call: telebot.types.CallbackQuery) -> None:
    action = call.data.split(":", 1)[1] if ":" in call.data else ""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")

    if action == "close":
        try:
            await tg_bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "settings":
        cfg_text = _config_text("tg", chat_id, user_id)
        kb = build_main_config_keyboard("tg", chat_id, user_id)
        try:
            await tg_bot.edit_message_text(
                cfg_text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=kb,
            )
            config_msg_owners[call.message.message_id] = user_id
        except Exception as e:
            logger.warning(f"menu:settings edit: {e}")
        await tg_bot.answer_callback_query(call.id)
        return

    if action == "help":
        await tg_bot.answer_callback_query(call.id)
        # Заменяем сообщение на rich help, чтобы форматирование таблицы/H1 сохранилось
        edited = await edit_rich_message(chat_id, call.message.message_id, HELP_TEXT)
        if not edited:
            # fallback: удаляем и отправляем заново
            try:
                await tg_bot.delete_message(chat_id, call.message.message_id)
            except Exception:
                pass
            await send_formatted(chat_id, HELP_TEXT)
        return

    if action == "open":
        await tg_bot.answer_callback_query(call.id)
        menu_text = _build_menu_text("tg", chat_id, user_id)
        kb = build_menu_keyboard("tg", chat_id, user_id)
        edited = await edit_rich_message(chat_id, call.message.message_id, menu_text, reply_markup=kb)
        if not edited:
            try:
                await tg_bot.delete_message(chat_id, call.message.message_id)
            except Exception:
                pass
            await send_formatted(chat_id, menu_text, reply_markup=kb)
        return

# ============================================================
# TELEGRAM: HELP / MENU / START / DONATE
# ============================================================
HELP_TEXT = (
    "# Кульш — команды\n\n"
    "**Общие**\n"
    "- `/start` — приветствие\n"
    "- `/menu` — интерактивное меню\n"
    "- `/help` — эта справка\n"
    "- `/donate` — поддержка проекта\n"
    "- `/donate_stars <N>` — донат через Telegram Stars\n"
    "- `/credits` — баланс кредитов\n\n"
    "**Настройки**\n"
    "- `кульш конфиг` / `кульш настройки` — панель настроек\n\n"
    "**Утилиты**\n"
    "- `кульш аватарка` — описать аватарку собеседника\n"
    "- `кульш вспомни медиа [N]` — вспомнить последние N медиа\n"
    "- `кульш логи` — логи сервера (админам)\n\n"
    "**Развлечения**\n"
    "- `кульш psl` — оценка внешности (looksmaxxing)\n"
    "- `кульш psl совет` — оценка с рекомендациями\n"
    "- `кульш battle` — баттл двух фото (одним альбомом)\n"
    "- `кульш донаты` — топ донатеров\n\n"
    "**Инструменты (в личных сообщениях)**\n"
    "Отправьте zip-архив или текстовый файл — бот обработает и вернёт результат.\n\n"
    f"Mini App: {MINI_APP_URL}\n"
    f"GitHub: {GITHUB_URL}"
)


async def _send_menu_gif(chat_id: int, reply_to: int | None, path: str, fallback_url: str) -> int | None:
    try:
        if os.path.exists(path):
            with open(path, 'rb') as gif:
                sent = await tg_bot.send_animation(
                    chat_id, InputFile(gif),
                    reply_to_message_id=reply_to,
                )
        else:
            sent = await tg_bot.send_animation(
                chat_id, fallback_url,
                reply_to_message_id=reply_to,
            )
        return sent.message_id
    except Exception as e:
        logger.warning(f"send menu gif failed ({path}): {e}")
        return None


@tg_bot.message_handler(commands=['start'])
async def handle_start(message: telebot.types.Message) -> None:
    args = telebot.util.extract_arguments(message.text or "")
    if args:
        if args.startswith('donate_stars_'):
            try:
                stars = int(args.split('_')[-1])
                if stars <= 0:
                    raise ValueError
            except (ValueError, IndexError):
                await reply_tg_html(message, "Неверное количество звёзд.")
                return
            pending_donations[message.chat.id] = stars
            prices = [telebot.types.LabeledPrice(label="Поддержать Кульша", amount=stars)]
            await tg_bot.send_invoice(
                chat_id=message.chat.id, title="Донат Кульшу",
                description=f"Поддержка разработки на {stars} ⭐",
                invoice_payload=f"donate_{stars}_stars", provider_token="",
                currency="XTR", prices=prices, start_parameter="donate",
            )
            return

    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id

    gif_msg_id = await _send_menu_gif(
        chat_id, message.message_id,
        path=KULSH_GIF_PATH,
        fallback_url=random.choice(GIF_POOL),
    )

    start_text = _build_start_text("tg", chat_id, user_id)
    kb = build_start_keyboard("tg", chat_id, user_id)
    reply_to = gif_msg_id if gif_msg_id else message.message_id
    await send_formatted(chat_id, start_text, reply_to=reply_to, reply_markup=kb)


@tg_bot.message_handler(commands=['menu'])
async def handle_menu(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")

    gif_path = MENU_GIF_EN_PATH if lang == "en" else MENU_GIF_RU_PATH

    gif_msg_id = await _send_menu_gif(
        chat_id, message.message_id,
        path=gif_path,
        fallback_url=random.choice(GIF_POOL),
    )

    menu_text = _build_menu_text("tg", chat_id, user_id)
    kb = build_menu_keyboard("tg", chat_id, user_id)
    reply_to = gif_msg_id if gif_msg_id else message.message_id
    await send_formatted(chat_id, menu_text, reply_to=reply_to, reply_markup=kb)


@tg_bot.message_handler(commands=['help'])
async def handle_help(message: telebot.types.Message) -> None:
    try:
        await send_formatted(
            message.chat.id, HELP_TEXT,
            reply_to=message.message_id,
        )
    except Exception:
        await tg_bot.send_message(
            message.chat.id, re.sub(r'<[^>]+>', '', HELP_TEXT),
            reply_to_message_id=message.message_id,
        )


@tg_bot.message_handler(commands=['donate'])
async def handle_donate(message: telebot.types.Message) -> None:
    text = (
        "# Поддержать Кульша\n\n"
        "Донаты идут на серверы, домены и дальнейшую разработку проекта.\n\n"
        "**Способы:**\n"
        f"- Онлайн-донат: {DONATE_URL}\n"
        "- Telegram Stars: `/donate_stars <количество>`\n\n"
        f"GitHub: {GITHUB_URL}"
    )
    try:
        await send_formatted(message.chat.id, text, reply_to=message.message_id)
    except Exception:
        await reply_tg_html(message, f"Поддержать Кульша: {DONATE_URL}")


@tg_bot.message_handler(commands=['donate_stars'])
async def handle_donate_stars(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    args = telebot.util.extract_arguments(message.text or "").strip()
    if not args:
        await reply_tg_html(
            message,
            "Укажите количество звёзд: <code>/donate_stars 100</code>\n"
            "Минимум — 1 звезда.",
        )
        return
    try:
        stars = int(args.split()[0])
        if stars <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await reply_tg_html(message, "Неверное количество звёзд. Пример: <code>/donate_stars 100</code>")
        return

    pending_donations[chat_id] = stars
    prices = [telebot.types.LabeledPrice(label="Поддержать Кульша", amount=stars)]
    try:
        await tg_bot.send_invoice(
            chat_id=chat_id,
            title="Донат Кульшу",
            description=f"Поддержка разработки на {stars} ⭐",
            invoice_payload=f"donate_{stars}_stars",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="donate",
            reply_to_message_id=message.message_id,
        )
    except Exception as e:
        logger.error(f"donate_stars invoice fail: {e}")
        await reply_tg_html(message, f"Не удалось выставить счёт: {e}")


@tg_bot.message_handler(commands=['credits'])
async def handle_credits(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    creds = get_user_credits("tg", message.from_user.id)
    await reply_tg_html(message, f"Кредиты: {creds}/{DAILY_CREDITS}")


@tg_bot.message_handler(commands=['togglepremiumfunctionsadmin'])
async def handle_toggle_premium(message: telebot.types.Message) -> None:
    global premium_functions_enabled
    if message.from_user is None or message.from_user.id != PREMIUM_ADMIN_ID:
        await reply_tg_html(message, "Нет доступа.")
        return
    premium_functions_enabled = not premium_functions_enabled
    state = "включены" if premium_functions_enabled else "выключены"
    await reply_tg_html(message, f"Расширенные функции: {state}")


@tg_bot.pre_checkout_query_handler(func=lambda query: True)
async def handle_pre_checkout(pre_checkout: telebot.types.PreCheckoutQuery) -> None:
    await tg_bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@tg_bot.message_handler(content_types=['successful_payment'])
async def handle_successful_payment(message: telebot.types.Message) -> None:
    if message.successful_payment is None or message.from_user is None:
        return
    payment = message.successful_payment
    user_id = message.chat.id
    try:
        stars = pending_donations.pop(user_id, None) or int(payment.invoice_payload.split('_')[1])
    except Exception:
        stars = 0
    name = message.from_user.full_name or message.from_user.username or str(user_id)
    logger.info(f"{user_id} задонатил {stars} звёзд")
    add_donation('tg', user_id, stars, name)
    await send_donation_alert('tg', name, stars)
    await reply_tg_html(message, f"Спасибо за поддержку — {stars} ⭐")

# ============================================================
# TG CONFIG / AVATAR / RECALL
# ============================================================
async def tg_handle_config(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_key = get_chat_key("tg", chat_id)
    config_trigger_msgs[chat_key] = message.message_id
    try:
        sent = await tg_bot.send_message(
            chat_id,
            _config_text("tg", chat_id, user_id),
            parse_mode='HTML',
            reply_markup=build_main_config_keyboard("tg", chat_id, user_id),
            reply_to_message_id=message.message_id,
        )
        config_msg_owners[sent.message_id] = user_id
    except Exception as e:
        logger.warning(f"Config send failed: {e}")
        try:
            await tg_bot.send_message(
                chat_id,
                re.sub(r'<[^>]+>', '', _config_text("tg", chat_id, user_id)),
                reply_markup=build_main_config_keyboard("tg", chat_id, user_id),
            )
        except Exception as e2:
            logger.error(f"Config fallback fail: {e2}")


async def tg_handle_avatar(message: telebot.types.Message, chat_id: int, user_id: int) -> None:
    raw = await get_avatar_description_tg(message, chat_id, user_id)
    if not raw:
        await reply_tg_html(message, "не удалось получить аватарку")
        return
    segments = clean_extra_text(raw)
    if not segments:
        await reply_tg_html(message, "не удалось получить аватарку")
        return
    for i, seg in enumerate(segments):
        if i == 0:
            await reply_tg_html(message, seg)
        else:
            await send_tg_html(message.chat.id, seg)


async def tg_handle_recall_media(message: telebot.types.Message, chat_id: int, user_id: int, parts: list[str]) -> None:
    n = 3
    for p in parts:
        if p.isdigit():
            n = min(int(p), 10)
            break
    raw = await get_recall_media_description_tg(message, chat_id, user_id, n)
    if not raw:
        await reply_tg_html(message, "ничего не найдено в памяти")
        return
    segments = clean_extra_text(raw)
    if not segments:
        await reply_tg_html(message, "ничего не найдено в памяти")
        return
    for i, seg in enumerate(segments):
        if i == 0:
            await reply_tg_html(message, seg)
        else:
            await send_tg_html(message.chat.id, seg)

# ============================================================
# UTILITY EXECUTION
# ============================================================
async def execute_utility_tg(message: telebot.types.Message, marker: str, chat_id: int, user_id: int) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    if marker in ("sticker", "gif"):
        if not cfg.get("stickers_enabled", True):
            return
        try:
            await tg_bot.send_sticker(message.chat.id, random.choice(STICKER_POOL))
        except Exception as e:
            logger.error(f"sticker error: {e}")


async def execute_utility_ds(message: discord.Message, marker: str, chat_id: int, user_id: int) -> None:
    cfg = get_user_config("ds", chat_id, user_id)
    if marker in ("sticker", "gif"):
        if not cfg.get("stickers_enabled", True):
            return
        try:
            gif_url = random.choice(GIF_POOL)
            embed = discord.Embed().set_image(url=gif_url)
            await message.reply(embed=embed)
        except Exception as e:
            logger.error(f"gif error: {e}")

# ============================================================
# STREAMING HELPERS
# ============================================================
async def _stream_text_via_drafts(chat_id: int, text: str, is_private: bool = True) -> bool:
    if not premium_functions_enabled:
        return False
    if not is_private:
        return False
    draft_id = random.randint(1, 2 ** 30)
    words = text.split()
    if not words:
        return False
    acc = ""
    chunk_size = max(1, len(words) // 15)
    for i, w in enumerate(words):
        acc = (acc + " " + w).strip()
        if i % chunk_size == 0 or i == len(words) - 1:
            ok = await stream_draft(chat_id, draft_id, acc)
            if not ok:
                return False
            await asyncio.sleep(0.06)
    return True

# ============================================================
# SEND TG AI RESPONSE
# ============================================================
async def send_tg_ai_response(message: telebot.types.Message, chat_id: int, user_id: int, answer_raw: str) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    separate_enabled = cfg.get("separate_enabled", True)
    streaming = cfg.get("streaming_enabled", False) and premium_functions_enabled

    if streaming and separate_enabled:
        streaming = False

    clean_segments, markers = process_ai_response(answer_raw, separate_enabled=separate_enabled)

    extra_segments: list[str] = []
    if "avatar" in markers:
        markers.remove("avatar")
        try:
            ar = await get_avatar_description_tg(message, chat_id, user_id)
            if ar:
                extra_segments.extend(clean_extra_text(ar))
        except Exception as e:
            logger.warning(f"avatar desc failed: {e}")
    if "recall_media" in markers:
        markers.remove("recall_media")
        try:
            rr = await get_recall_media_description_tg(message, chat_id, user_id, 3)
            if rr:
                extra_segments.extend(clean_extra_text(rr))
        except Exception as e:
            logger.warning(f"recall desc failed: {e}")

    all_segments = clean_segments + extra_segments

    if not all_segments:
        for m in markers:
            try:
                await execute_utility_tg(message, m, chat_id, user_id)
            except Exception as e:
                logger.warning(f"utility {m}: {e}")
        return

    is_private_chat = (message.chat.type == 'private')

    for i, seg in enumerate(all_segments):
        try:
            await typing_with_delay_tg(message.chat.id, seg)
        except Exception:
            pass

        if streaming and i == 0 and len(seg) > 60 and is_private_chat:
            try:
                await _stream_text_via_drafts(message.chat.id, seg, is_private=True)
            except Exception as e:
                logger.debug(f"stream fail: {e}")

        sent_ok = False
        try:
            sent_ok = await send_rich_message(
                message.chat.id, seg,
                reply_to=message.message_id if i == 0 else None,
            )
        except Exception as e:
            logger.debug(f"rich fail: {e}")

        if not sent_ok:
            try:
                if i == 0:
                    await send_tg_html(message.chat.id, seg, reply_to=message.message_id)
                else:
                    await send_tg_html(message.chat.id, seg)
            except Exception as e:
                logger.error(f"send_tg_html fail: {e}")

        add_bot_memory(f"tg_{message.chat.id}", seg)

    for m in markers:
        if m in ("sticker", "gif"):
            try:
                await execute_utility_tg(message, m, chat_id, user_id)
            except Exception as e:
                logger.warning(f"utility {m}: {e}")

# ============================================================
# OLD MESSAGE REPLY (TG)
# ============================================================
async def maybe_reply_to_old_message_tg(message: telebot.types.Message, chat_id: int, user_id: int) -> None:
    chat_key = f"tg_{chat_id}"
    now = time.time()
    if now - last_old_reply.get(chat_key, 0) < 600:
        return
    if random.random() > 0.12:
        return
    mem = list(get_chat_memory(chat_key))
    candidates = [e for e in mem[:-2] if e.get("type") == "user" and e.get("text")]
    if not candidates:
        return
    old = random.choice(candidates)
    try:
        comment = await ask_ai_async(
            prompt=(f"Ты видишь старое сообщение от {old.get('display','?')}: \"{old.get('text','')}\". "
                    f"Хочешь коротко прокомментировать? Если да — одно короткое сообщение в стиле Кульша. "
                    f"Если нет — ответь ровно 'НЕТ'."),
            system_instruction_override="Ты Кульш. Одним коротким сообщением или 'НЕТ'. Без markdown.",
            chat_id=chat_id, user_id=user_id,
        )
        if comment and comment.strip() and comment.strip().upper() != "НЕТ":
            last_old_reply[chat_key] = now
            cfg = get_user_config("tg", chat_id, user_id)
            segments, markers = process_ai_response(comment, separate_enabled=cfg.get("separate_enabled", True))
            old_msg_id = old.get("message_id")
            for i, seg in enumerate(segments):
                try:
                    await typing_with_delay_tg(message.chat.id, seg)
                except Exception:
                    pass
                if i == 0 and old_msg_id:
                    await send_tg_html(message.chat.id, seg, reply_to=old_msg_id)
                else:
                    await send_tg_html(message.chat.id, seg)
                add_bot_memory(chat_key, seg)
            for m in markers:
                if m in ("sticker", "gif"):
                    try:
                        await execute_utility_tg(message, m, chat_id, user_id)
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"old reply tg: {e}")


async def should_random_reply(platform: str, chat_id: int, user_id: int) -> bool:
    cfg = get_user_config(platform, chat_id, user_id)
    if not cfg.get("random_reply_enabled", False):
        return False
    chat_key = f"{platform}_{chat_id}"
    now = time.time()
    if now - last_random_reply.get(chat_key, 0) < 900:
        return False
    if random.random() > 0.03:
        return False
    return True

# ============================================================
# TOOLS (архивы/файлы/консоль)
# ============================================================
TEXT_EXTS = {
    "txt", "py", "json", "html", "htm", "js", "css", "cs", "cpp", "c", "h", "hpp",
    "java", "php", "rb", "go", "rs", "ts", "tsx", "jsx", "xml", "yml", "yaml",
    "toml", "ini", "cfg", "conf", "sh", "bash", "bat", "ps1", "sql", "md",
    "log", "env", "gitignore", "dockerfile", "makefile", "vue", "svelte",
    "scss", "sass", "less", "kt", "swift", "dart", "lua", "pl", "r", "m", "mm",
}

SAFE_COMMANDS = {"ls", "cat", "head", "tail", "wc", "grep", "find", "file", "stat", "du", "tree", "pwd"}


def _safe_join(base: str, rel: str) -> str | None:
    if not rel:
        return base
    target = os.path.realpath(os.path.join(base, rel))
    base_real = os.path.realpath(base)
    if not target.startswith(base_real + os.sep) and target != base_real:
        return None
    return target


def _list_files(base: str) -> list[str]:
    out: list[str] = []
    for root, dirs, files in os.walk(base):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base)
            out.append(rel)
    return out


def _is_text_file(path: str) -> bool:
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
        if b'\x00' in chunk:
            return False
        chunk.decode('utf-8', errors='strict')
        return True
    except Exception:
        return False


async def extract_archive(zip_path: str, dest_dir: str) -> list[str]:
    def _do():
        with zipfile.ZipFile(zip_path, 'r') as zf:
            total = 0
            count = 0
            for info in zf.infolist():
                if info.is_dir():
                    continue
                count += 1
                if count > MAX_FILES:
                    raise Exception("Слишком много файлов в архиве")
                total += info.file_size
                if total > MAX_TOTAL_UNPACKED:
                    raise Exception("Распакованный архив слишком большой")
                target = _safe_join(dest_dir, info.filename)
                if target is None:
                    raise Exception(f"Небезопасный путь: {info.filename}")
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(info) as src, open(target, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        return _list_files(dest_dir)
    return await asyncio.to_thread(_do)


async def create_archive(source_dir: str, out_zip: str) -> None:
    def _do():
        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, source_dir)
                    zf.write(full, rel)
    await asyncio.to_thread(_do)


async def run_safe_command(base_dir: str, cmd: str) -> tuple[int, str]:
    parts = cmd.strip().split()
    if not parts:
        return 1, "пустая команда"
    prog = parts[0].lower()
    if prog not in SAFE_COMMANDS:
        return 1, f"команда '{prog}' не разрешена"
    for p in parts:
        if any(ch in p for ch in (';', '&', '|', '`', '$', '<', '>', '\n')):
            return 1, "метасимволы запрещены"
    try:
        proc = await asyncio.create_subprocess_exec(
            *parts, cwd=base_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        out = (stdout or b'').decode('utf-8', errors='replace')[:8000]
        err = (stderr or b'').decode('utf-8', errors='replace')[:2000]
        if err:
            out += "\n[stderr]\n" + err
        return proc.returncode or 0, out
    except asyncio.TimeoutError:
        return 1, "команда не завершилась за 15 сек"
    except Exception as e:
        return 1, f"ошибка: {e}"


async def tool_edit_archive(message: telebot.types.Message, user_request: str,
                            archive_bytes: bytes, filename: str) -> None:
    user_id = message.from_user.id
    chat_id = message.chat.id
    status = await tg_bot.send_message(chat_id, "Распаковываю архив...")
    work_dir = tempfile.mkdtemp(prefix="kulsh_tools_")
    tools_sessions[chat_id] = {"dir": work_dir, "user_id": user_id}
    try:
        arch_path = os.path.join(work_dir, "input.zip")
        with open(arch_path, 'wb') as f:
            f.write(archive_bytes)
        files = await extract_archive(arch_path, work_dir)
        files_display = ", ".join(files[:30])
        if len(files) > 30:
            files_display += f" ... (+{len(files) - 30})"
        await tg_bot.edit_message_text(f"Распаковано:\n\n{files_display}",
                                       chat_id, status.message_id)

        contents: dict[str, str] = {}
        for rel in files[:50]:
            full = _safe_join(work_dir, rel)
            if full and os.path.exists(full) and os.path.getsize(full) < MAX_FILE_SIZE:
                if _is_text_file(full):
                    try:
                        with open(full, 'r', encoding='utf-8', errors='replace') as f:
                            contents[rel] = f.read()
                    except Exception:
                        pass
        files_context = "\n\n".join(f"=== {fn} ===\n{c[:6000]}" for fn, c in contents.items())
        if len(files_context) > 60000:
            files_context = files_context[:60000] + "\n...[обрезано]"

        await tg_bot.edit_message_text(f"Анализирую {len(contents)} файл(ов)...",
                                       chat_id, status.message_id)

        prompt = (
            f"Пользователь отправил архив '{filename}' и попросил:\n\n{user_request}\n\n"
            f"Содержимое:\n{files_context}\n\n"
            "Верни JSON-объект строго:\n"
            '{"summary": "краткое описание (на русском, дружелюбно, в стиле Кульша)", '
            '"files": {"путь": "полное новое содержимое файла", ...}}\n\n'
            "Включай в 'files' только изменённые/новые файлы. Только JSON, без markdown."
        )
        raw = await ask_ai_async(
            prompt=prompt,
            system_instruction_override=(
                "Ты инструмент редактирования кода. Отвечай ТОЛЬКО валидным JSON с полями 'summary' и 'files'. "
                "Никаких пояснений, markdown или текста."
            ),
            chat_id=chat_id, user_id=user_id, platform="tg",
        )
        try:
            data = json.loads(clean_json_text(raw))
        except Exception as e:
            await tg_bot.edit_message_text(f"Не удалось распарсить ответ ИИ: {e}",
                                           chat_id, status.message_id)
            return

        summary = data.get("summary", "готово")
        new_files = data.get("files", {})
        if not isinstance(new_files, dict) or not new_files:
            await tg_bot.edit_message_text(f"ИИ не предложил изменений. {summary}",
                                           chat_id, status.message_id)
            return

        await tg_bot.edit_message_text(f"Редактирую {len(new_files)} файл(ов)...",
                                       chat_id, status.message_id)
        for rel, new_content in new_files.items():
            full = _safe_join(work_dir, rel)
            if full is None:
                continue
            os.makedirs(os.path.dirname(full) or work_dir, exist_ok=True)
            with open(full, 'w', encoding='utf-8') as f:
                f.write(new_content)

        await tg_bot.edit_message_text("Собираю архив обратно...",
                                       chat_id, status.message_id)
        out_zip = os.path.join(work_dir, f"edited_{filename or 'archive.zip'}")
        await create_archive(work_dir, out_zip)

        await tg_bot.edit_message_text("Отправляю готовый архив...",
                                       chat_id, status.message_id)
        with open(out_zip, 'rb') as f:
            await tg_bot.send_document(
                chat_id, InputFile(f, file_name=os.path.basename(out_zip)),
                caption=summary,
            )
        await tg_bot.edit_message_text("Готово", chat_id, status.message_id)
    except Exception as e:
        logger.error(f"tool_edit_archive: {e}")
        try:
            await tg_bot.edit_message_text(f"Ошибка: {e}", chat_id, status.message_id)
        except Exception:
            pass
    finally:
        try:
            if work_dir and os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
        tools_sessions.pop(chat_id, None)


async def tool_review_file(message: telebot.types.Message, user_request: str,
                           file_bytes: bytes, filename: str) -> None:
    user_id = message.from_user.id
    chat_id = message.chat.id
    try:
        text = file_bytes.decode('utf-8', errors='replace')
    except Exception:
        await reply_tg_html(message, "не удалось прочитать файл как текст")
        return
    if len(text) > MAX_FILE_SIZE:
        text = text[:MAX_FILE_SIZE] + "\n...[обрезано]"
    prompt = (
        f"Пользователь отправил файл '{filename}' и просит:\n\n{user_request}\n\n"
        f"Содержимое файла:\n```\n{text}\n```\n\n"
        "Ответь в стиле Кульша: коротко разбери, ответь на вопрос. Не редактируй файл."
    )
    answer = await ask_ai_async(prompt=prompt, chat_id=chat_id, user_id=user_id, platform="tg")
    await send_tg_ai_response(message, chat_id, user_id, answer)

# ============================================================
# TG MEDIA HANDLER
# ============================================================
@tg_bot.message_handler(content_types=['photo', 'video', 'animation', 'document', 'sticker'])
async def handle_tg_media(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_dm = message.chat.type == 'private'
    caption = message.caption or ""
    cl = caption.lower()
    chat_key = f"tg_{chat_id}"

    display_name = message.from_user.full_name or "Unknown"
    username = message.from_user.username or ""

    media_tag = None
    file_id = None
    media_type = None
    file_name = None
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
        media_tag = "[фото]"
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
        media_tag = "[видео]"
    elif message.animation:
        file_id = message.animation.file_id
        media_type = "animation"
        media_tag = "[гифка]"
    elif message.document:
        file_id = message.document.file_id
        media_type = "document"
        file_name = message.document.file_name or "file"
        media_tag = f"[док: {file_name}]"
    elif message.sticker:
        file_id = message.sticker.file_id
        media_type = "sticker"
        media_tag = "[стикер]"

    if file_id and media_tag:
        add_media_history(chat_key, None, media_type, display_name, file_id=file_id, caption=caption)

    if is_battle_command(caption) and message.photo:
        if message.media_group_id:
            mgid = message.media_group_id
            if mgid not in battle_photos:
                battle_photos[mgid] = []
                battle_media_groups[mgid] = asyncio.create_task(
                    process_battle_media_group(mgid, chat_id, user_id)
                )
            img_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
            battle_photos[mgid].append(img_bytes)
        else:
            await reply_tg_html(message, "Для баттла нужно два фото. Отправьте их одним альбомом.")
        return

    if message.media_group_id and message.media_group_id in battle_photos and message.photo:
        img_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
        battle_photos[message.media_group_id].append(img_bytes)
        return

    is_looksmaxxing = (
        is_looksmaxxing_command(caption) or
        (message.reply_to_message and message.reply_to_message.from_user
         and message.reply_to_message.from_user.id == (tg_bot.user.id if tg_bot.user else 0)
         and message.reply_to_message.text
         and is_looksmaxxing_command(message.reply_to_message.text)) or
        user_looksmaxxing_state.get(chat_id, False)
    )
    if is_looksmaxxing and message.photo:
        user_looksmaxxing_state[chat_id] = False
        status = await tg_bot.send_message(chat_id, "Анализирую внешность...")
        try:
            img_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
            include_advice = ("совет" in cl or "advice" in cl or
                              (message.reply_to_message and message.reply_to_message.text and
                               ("совет" in message.reply_to_message.text.lower()
                                or "advice" in message.reply_to_message.text.lower())))
            cfg = get_user_config("tg", chat_id, user_id)
            lang = cfg.get("language", "ru")
            theme = cfg.get("theme", "dark")
            ai_data = await get_looksmaxxing_data(img_bytes, include_advice, lang=lang)
            if "error" in ai_data:
                await tg_bot.edit_message_text(f"Ошибка: {ai_data['error']}", chat_id, status.message_id)
                return
            infographic = await create_infographic(img_bytes, ai_data, theme=theme, lang=lang)
            report_text = (
                f"<b>РЕЗУЛЬТАТЫ LOOKSMAXXING</b>\n\n"
                f"Пол: {ai_data.get('gender', '?')}\n"
                f"PSL: <code>{ai_data.get('psl', '?')}/8.0</code>\n"
                f"Tier: <code>{ai_data.get('tier', '?')}</code>\n"
            )
            if ai_data.get("potential"):
                report_text += f"Потенциал: <code>{ai_data['potential']}</code>\n"
            report_text += f"\n<b>Анализ:</b>\n{html.escape(ai_data.get('summary', ''))}"
            if include_advice and ai_data.get("advice"):
                report_text += f"\n\n<b>Рекомендации:</b>\n{html.escape(ai_data['advice'])}"
            try:
                await tg_bot.send_photo(chat_id, InputFile(infographic),
                                        caption="Результаты looksmaxxing")
            except Exception as e:
                logger.error(f"infographic send: {e}")
            for chunk in [report_text[i:i + 3900] for i in range(0, len(report_text), 3900)]:
                try:
                    await tg_bot.send_message(chat_id, chunk, parse_mode='HTML')
                except Exception:
                    await tg_bot.send_message(chat_id, re.sub(r'<[^>]+>', '', chunk))
            await tg_bot.delete_message(chat_id, status.message_id)
            add_user_memory(chat_key, "TG", display_name, username, user_id,
                            f"[looksmaxxing] {caption}", ["photo"], message_id=message.message_id)
            add_bot_memory(chat_key, "[looksmaxxing отчёт]")
        except Exception as e:
            logger.error(f"looksmaxxing: {e}")
            await reply_tg_html(message, f"Ошибка: {e}")
        return

    if is_dm and message.document:
        mime = message.document.mime_type or ""
        doc_name = message.document.file_name or ""
        ext = doc_name.lower().rsplit('.', 1)[-1] if '.' in doc_name else ""

        if ext == "zip":
            credits = get_user_credits("tg", user_id)
            if credits < COST_ARCHIVE_EDIT:
                await reply_tg_html(
                    message,
                    f"Недостаточно кредитов для редактирования архива.\n"
                    f"Нужно {COST_ARCHIVE_EDIT}, у вас {credits}/{DAILY_CREDITS}.",
                )
                return
            spend_credits("tg", user_id, COST_ARCHIVE_EDIT)
            try:
                file_bytes = await get_tg_file_bytes(tg_bot, message.document.file_id)
            except Exception as e:
                await reply_tg_html(message, f"не удалось скачать файл: {e}")
                return
            await tool_edit_archive(message, caption.strip() or "отредактируй что-нибудь полезное",
                                    file_bytes, doc_name or "archive.zip")
            return

        if ext in TEXT_EXTS or mime.startswith("text/"):
            try:
                file_bytes = await get_tg_file_bytes(tg_bot, message.document.file_id)
            except Exception as e:
                await reply_tg_html(message, f"не удалось скачать файл: {e}")
                return
            await tool_review_file(message, caption.strip() or "что тут?", file_bytes, doc_name or "file")
            return

    is_reply_to_bot = (message.reply_to_message and message.reply_to_message.from_user
                       and message.reply_to_message.from_user.id == (tg_bot.user.id if tg_bot.user else 0))
    addressed = bool(is_reply_to_bot or re.search(r'(?i)\bкульш\b', caption) or is_dm)

    if not addressed:
        add_user_memory(chat_key, "TG", display_name, username, user_id, caption or "",
                        [media_tag or "медиа"], message_id=message.message_id)
        if await should_random_reply("tg", chat_id, user_id):
            answer = await ask_ai_async(
                context_type="observer",
                messages=memory_to_messages(get_chat_memory(chat_key)),
                chat_id=chat_id, user_id=user_id, platform="tg",
            )
            if answer and answer.strip() and answer.strip().upper() != "НЕТ":
                last_random_reply[chat_key] = time.time()
                await send_tg_ai_response(message, chat_id, user_id, answer)
        return

    await tg_bot.send_chat_action(chat_id, 'typing')
    image_bytes = None
    image_mime = "image/jpeg"
    try:
        if message.photo:
            image_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
        elif message.animation:
            vid = await get_tg_file_bytes(tg_bot, message.animation.file_id)
            frame = await extract_video_frame(vid, ".mp4")
            if frame:
                image_bytes = frame
        elif message.video:
            vid = await get_tg_file_bytes(tg_bot, message.video.file_id)
            frame = await extract_video_frame(vid, ".mp4")
            if frame:
                image_bytes = frame
        elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
            image_bytes = await get_tg_file_bytes(tg_bot, message.document.file_id)
            image_mime = message.document.mime_type
    except Exception as e:
        logger.warning(f"download media: {e}")

    prompt = caption.strip() or "что на этом?"
    add_user_memory(chat_key, "TG", display_name, username, user_id,
                    f"{prompt} [с медиа: {media_tag}]", [media_tag or "медиа"],
                    message_id=message.message_id)
    messages = memory_to_messages(get_chat_memory(chat_key))
    answer = await ask_ai_async(messages=messages, image_bytes=image_bytes,
                                image_mime=image_mime, chat_id=chat_id,
                                user_id=user_id, platform="tg")
    await send_tg_ai_response(message, chat_id, user_id, answer)
    asyncio.create_task(extract_memory(chat_key, f"{display_name}: [медиа] {caption}", answer))

# ============================================================
# TG TEXT HANDLER
# ============================================================
@tg_bot.message_handler(func=lambda m: m.text is not None, content_types=['text'])
async def handle_tg_text(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_dm = message.chat.type == 'private'
    text = cast(str, message.text or "")
    tl = text.lower()
    display_name = message.from_user.full_name or "Unknown"
    username = message.from_user.username or ""
    chat_key = f"tg_{chat_id}"

    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")

    # Ожидание кастомного промпта (ответ на ForceReply-сообщение)
    if user_id in prompt_waiting:
        waiting_msg_id = prompt_waiting[user_id]
        # проверяем, что это ответ на наше сообщение, либо это просто следующее сообщение от того же юзера
        is_reply_to_ask = bool(
            message.reply_to_message and message.reply_to_message.message_id == waiting_msg_id
        )
        # Также принимаем любой текст, если пользователь ещё в режиме ожидания
        if is_reply_to_ask or True:
            prompt_waiting.pop(user_id, None)
            new_prompt = text.strip()
            if new_prompt.lower() in ("отмена", "cancel", "/cancel", "отменить"):
                cfg["custom_prompt"] = None
                try:
                    await tg_bot.edit_message_text(
                        _localize(lang, "Изменение промпта отменено.", "Prompt edit cancelled."),
                        chat_id, waiting_msg_id,
                    )
                except Exception:
                    pass
            else:
                truncated = new_prompt[:2000]
                cfg["custom_prompt"] = truncated
                try:
                    await tg_bot.edit_message_text(
                        _localize(
                            lang,
                            f"Промпт сохранён ({len(truncated)} символов).",
                            f"Prompt saved ({len(truncated)} chars).",
                        ),
                        chat_id, waiting_msg_id,
                    )
                except Exception:
                    pass
            return

    if tl.startswith("кульш конфиг") or tl.startswith("кульш настройки"):
        await tg_handle_config(message)
        return

    if tl.startswith("кульш донаты"):
        top = get_top_donators()
        if not top:
            await reply_tg_html(message, "Пока никто не донатил. Будь первым.\n" + DONATE_URL)
            return
        lines = ["# Топ донатеров\n"]
        for i, (name, total) in enumerate(top, 1):
            lines.append(f"{i}. {html.escape(name)} — {total} очков")
        await send_formatted(chat_id, "\n".join(lines), reply_to=message.message_id)
        return

    if tl.startswith("кульш аватарк") or tl.startswith("кульш аватар") or tl.strip() in ("!avatar", "! avatar"):
        await tg_handle_avatar(message, chat_id, user_id)
        return

    if tl.startswith("кульш вспомни медиа") or "!recall_media" in tl:
        await tg_handle_recall_media(message, chat_id, user_id, text.split())
        return

    if tl.startswith("кульш логи"):
        if user_id != PREMIUM_ADMIN_ID:
            try:
                member = await tg_bot.get_chat_member(chat_id, user_id)
                if member.status not in ('administrator', 'creator'):
                    await reply_tg_html(message, "недостаточно прав")
                    return
            except Exception:
                await reply_tg_html(message, "не удалось проверить права")
                return
        try:
            tail = read_log_tail(20)
            full_caption = f"{LOG_INTRO}\n\n{tail}"
            if len(full_caption) <= 1024:
                caption = full_caption
                extra_text = None
            else:
                available = 1024 - len(LOG_INTRO) - 5
                caption = f"{LOG_INTRO}\n\n{tail[:available]}..."
                extra_text = tail
            try:
                with open('bot.log', 'rb') as logf:
                    await tg_bot.send_document(chat_id, InputFile(logf), caption=caption)
            except FileNotFoundError:
                await send_tg_html(chat_id, full_caption[:4000], reply_to=message.message_id)
                return
            if extra_text:
                for chunk in chunk_text(extra_text, 3900):
                    try:
                        await tg_bot.send_message(chat_id, f"<pre>{html.escape(chunk)}</pre>",
                                                  parse_mode='HTML')
                    except Exception:
                        await tg_bot.send_message(chat_id, chunk)
        except Exception as e:
            await reply_tg_html(message, f"Ошибка чтения логов: {e}")
        return

    if is_looksmaxxing_command(text):
        user_looksmaxxing_state[chat_id] = True
        add_user_memory(chat_key, "TG", display_name, username, user_id, text, message_id=message.message_id)
        await reply_tg_html(message, "Отправьте фото для анализа.")
        return

    if is_battle_command(text):
        add_user_memory(chat_key, "TG", display_name, username, user_id, text, message_id=message.message_id)
        await reply_tg_html(message, "Пришлите два фото одним альбомом с командой `кульш баттл`.")
        return

    is_reply_to_bot = (message.reply_to_message and message.reply_to_message.from_user
                       and message.reply_to_message.from_user.id == (tg_bot.user.id if tg_bot.user else 0))
    addressed = bool(is_reply_to_bot or re.search(r'(?i)\bкульш\b', text) or is_dm)

    if addressed:
        try:
            await tg_bot.send_chat_action(chat_id, 'typing')
        except Exception:
            pass
        add_user_memory(chat_key, "TG", display_name, username, user_id, text, message_id=message.message_id)
        messages = memory_to_messages(get_chat_memory(chat_key))
        answer = await ask_ai_async(messages=messages, chat_id=chat_id, user_id=user_id, platform="tg")
        await send_tg_ai_response(message, chat_id, user_id, answer)
        asyncio.create_task(extract_memory(chat_key, f"{display_name}: {text}", answer))
        asyncio.create_task(maybe_reply_to_old_message_tg(message, chat_id, user_id))
        return

    add_user_memory(chat_key, "TG", display_name, username, user_id, text, message_id=message.message_id)

    if await should_random_reply("tg", chat_id, user_id):
        try:
            answer = await ask_ai_async(
                context_type="observer",
                messages=memory_to_messages(get_chat_memory(chat_key)),
                chat_id=chat_id, user_id=user_id, platform="tg",
            )
            if answer and answer.strip() and answer.strip().upper() != "НЕТ":
                last_random_reply[chat_key] = time.time()
                await send_tg_ai_response(message, chat_id, user_id, answer)
        except Exception as e:
            logger.warning(f"Random reply: {e}")

# ============================================================
# BATTLE MEDIA GROUP
# ============================================================
async def process_battle_media_group(media_group_id: str, tg_chat_id: int, user_id: int):
    for _ in range(10):
        if media_group_id in battle_photos and len(battle_photos[media_group_id]) >= 2:
            break
        await asyncio.sleep(0.5)
    if media_group_id not in battle_photos or len(battle_photos[media_group_id]) < 2:
        battle_photos.pop(media_group_id, None)
        battle_media_groups.pop(media_group_id, None)
        await tg_bot.send_message(tg_chat_id, "Нужно два фото для баттла.")
        return
    photos = battle_photos.pop(media_group_id)
    battle_media_groups.pop(media_group_id, None)
    photo1_bytes, photo2_bytes = photos[:2]
    cfg = get_user_config("tg", tg_chat_id, user_id)
    lang = cfg.get("language", "ru")
    theme = cfg.get("theme", "dark")
    try:
        await tg_bot.send_chat_action(tg_chat_id, 'typing')
    except Exception:
        pass
    status = await tg_bot.send_message(tg_chat_id, "Сравниваю лица...")
    ai_data = await get_battle_data(photo1_bytes, photo2_bytes, lang=lang)
    if "error" in ai_data:
        await tg_bot.edit_message_text(f"Ошибка: {ai_data['error']}", tg_chat_id, status.message_id)
        return
    battle_img = await create_battle_infographic(photo1_bytes, photo2_bytes, ai_data,
                                                  theme=theme, lang=lang)
    winner_num = str(ai_data.get("winner", "1"))
    winner_label = "Первое фото" if winner_num == "1" else "Второе фото"
    report_text = (
        f"<b>РЕЗУЛЬТАТ БАТТЛА</b>\n\n"
        f"Победитель: <b>{winner_label}</b>\n"
        f"Причина: {html.escape(ai_data.get('reason', ''))}\n\n"
        f"Фото 1: PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
        f"Tier {html.escape(ai_data.get('photo1', {}).get('tier', '?'))}\n"
        f"Фото 2: PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
        f"Tier {html.escape(ai_data.get('photo2', {}).get('tier', '?'))}\n"
    )
    try:
        await tg_bot.send_photo(tg_chat_id, InputFile(battle_img), caption="Результат баттла")
    except Exception as e:
        logger.error(f"battle infra: {e}")
    try:
        await tg_bot.send_message(tg_chat_id, report_text, parse_mode='HTML')
    except Exception:
        await tg_bot.send_message(tg_chat_id, re.sub(r'<[^>]+>', '', report_text))
    await tg_bot.delete_message(tg_chat_id, status.message_id)

# ============================================================
# SAFE GIT UPDATE
# ============================================================
def _run_git(args: list[str], cwd: str, timeout: int = 60) -> tuple[int, str, str]:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError:
        return 127, "", "git not found"
    except Exception as e:
        return 1, "", str(e)


def _check_python_syntax(fpath: str) -> str | None:
    try:
        with open(fpath, 'r', encoding='utf-8') as fp:
            src = fp.read()
    except Exception as e:
        return f"read error: {type(e).__name__}: {e}"
    try:
        compile(src, fpath, 'exec')
    except SyntaxError as se:
        return f"SyntaxError: {se.msg} (line {se.lineno})"
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    return None


def _safe_check_import(fpath: str, timeout: int = 45) -> str | None:
    if not os.path.isfile(fpath):
        return None
    script = (
        "import importlib.util, sys, os\n"
        f"p = {fpath!r}\n"
        "spec = importlib.util.spec_from_file_location('_kulsh_check_mod', p)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "try:\n"
        "    spec.loader.exec_module(mod)\n"
        "except SystemExit:\n"
        "    pass\n"
        "except BaseException as e:\n"
        "    sys.stderr.write(f'{type(e).__name__}: {e}')\n"
        "    sys.exit(2)\n"
    )
    try:
        r = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.dirname(os.path.abspath(fpath)) or os.getcwd(),
        )
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "unknown").strip()
            return err[:800]
    except subprocess.TimeoutExpired:
        return "timeout при проверке импорта"
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    return None


def _find_entry_file(repo_path: str) -> str | None:
    try:
        cur = os.path.abspath(__file__)
        if os.path.exists(cur) and cur.startswith(os.path.abspath(repo_path)):
            return cur
    except Exception:
        pass
    for cand in ("main.py", "app.py", "bot.py"):
        p = os.path.join(repo_path, cand)
        if os.path.isfile(p):
            return p
    try:
        for f in os.listdir(repo_path):
            if f.endswith(".py") and not f.startswith("_"):
                return os.path.join(repo_path, f)
    except Exception:
        pass
    return None


async def perform_safe_git_update(repo_path: str) -> tuple[str, str]:
    rc, out, err = _run_git(["rev-parse", "HEAD"], cwd=repo_path, timeout=10)
    if rc != 0 or not out.strip():
        return "error", f"git rev-parse: {err or out or 'unknown error'}"
    prev_hash = out.strip()

    rc, out, err = _run_git(["fetch", "origin", "main"], cwd=repo_path, timeout=60)
    if rc != 0:
        return "error", f"git fetch: {err or out or 'unknown error'}"

    rc, out, err = _run_git(["pull", "origin", "main", "--ff-only"], cwd=repo_path, timeout=60)
    pull_out = (out or "") + (err or "")
    if rc != 0:
        rc2, out2, err2 = _run_git(["pull", "origin", "main"], cwd=repo_path, timeout=60)
        pull_out += "\n" + (out2 or "") + (err2 or "")
        if rc2 != 0:
            return "error", f"git pull fail:\n{pull_out[:1500]}"

    if "Already up to date" in pull_out or "Already up-to-date" in pull_out:
        return "up_to_date", pull_out

    syntax_errors: list[str] = []
    try:
        for root, dirs, files in os.walk(repo_path):
            if '.git' in root.split(os.sep):
                continue
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                err_s = _check_python_syntax(fpath)
                if err_s:
                    rel = os.path.relpath(fpath, repo_path)
                    syntax_errors.append(f"{rel}: {err_s}")
    except Exception as e:
        syntax_errors.append(f"walk error: {type(e).__name__}: {e}")

    if syntax_errors:
        rc_reset, out_r, err_r = _run_git(["reset", "--hard", prev_hash], cwd=repo_path, timeout=30)
        if rc_reset != 0:
            return "error", (
                "ошибки в новом коде, но git reset --hard не удался:\n"
                + (err_r or out_r or "unknown")
                + "\n\nОшибки:\n" + "\n".join(syntax_errors[:10])
            )
        return "rolled_back", "\n".join(syntax_errors[:10])

    entry = _find_entry_file(repo_path)
    if entry:
        import_err = await asyncio.to_thread(_safe_check_import, entry)
        if import_err:
            rc_reset, out_r, err_r = _run_git(["reset", "--hard", prev_hash], cwd=repo_path, timeout=30)
            if rc_reset != 0:
                return "error", (
                    f"ошибка импорта: {import_err}\n"
                    f"git reset --hard не удался: {err_r or out_r or 'unknown'}"
                )
            return "rolled_back", f"import error:\n{import_err[:800]}"

    return "ok", pull_out

# ============================================================
# DISCORD: SEND AI RESPONSE
# ============================================================
async def send_ds_ai_response(message: discord.Message, chat_id: int, user_id: int, answer_raw: str) -> None:
    cfg = get_user_config("ds", chat_id, user_id)
    separate_enabled = cfg.get("separate_enabled", True)
    clean_segments, markers = process_ai_response(answer_raw, separate_enabled=separate_enabled)

    extra_segments: list[str] = []
    if "avatar" in markers:
        markers.remove("avatar")
        try:
            ar = await get_avatar_description_ds(message, chat_id, user_id)
            if ar:
                extra_segments.extend(clean_extra_text(ar))
        except Exception as e:
            logger.warning(f"DS avatar: {e}")
    if "recall_media" in markers:
        markers.remove("recall_media")
        history = list(chat_media_history.get(f"ds_{chat_id}", []))
        if history:
            last = history[-3:]
            lines = [f"- {it.get('type', 'media')} от {it.get('sender', '?')}: {(it.get('caption') or '')[:100]}"
                     for it in last]
            extra_segments.append("Недавние медиа:\n" + "\n".join(lines))

    all_segments = clean_segments + extra_segments
    if not all_segments:
        for m in markers:
            if m in ("sticker", "gif"):
                try:
                    await execute_utility_ds(message, m, chat_id, user_id)
                except Exception as e:
                    logger.warning(f"ds utility: {e}")
        return

    for i, seg in enumerate(all_segments):
        try:
            await typing_with_delay_ds(message.channel, seg)
        except Exception:
            pass
        if i == 0:
            try:
                await message.reply(seg)
            except Exception:
                await message.channel.send(seg)
        else:
            await message.channel.send(seg)
        add_bot_memory(f"ds_{chat_id}", seg)

    for m in markers:
        if m in ("sticker", "gif"):
            try:
                await execute_utility_ds(message, m, chat_id, user_id)
            except Exception as e:
                logger.warning(f"ds utility {m}: {e}")

# ============================================================
# DISCORD CONFIG (текстом)
# ============================================================
def _ds_config_embed(chat_id: int, user_id: int) -> discord.Embed:
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    series = "вкл" if cfg.get("series_reminder_enabled", True) else "выкл"
    stickers = "вкл" if cfg.get("stickers_enabled", True) else "выкл"
    sep = "вкл" if cfg.get("separate_enabled", True) else "выкл"
    autoreply = "вкл" if cfg.get("random_reply_enabled", False) else "выкл"
    random_msgs = "вкл" if cfg.get("random_messages_enabled", True) else "выкл"
    prompt = cfg.get("custom_prompt") or "стандартный"
    if len(prompt) > 900:
        prompt = prompt[:900] + "..."
    theme_disp = "тёмная" if cfg.get("theme", "dark") == "dark" else "светлая"
    lang_disp = "Русский" if lang == "ru" else "English"

    embed = discord.Embed(
        title="Настройки Кульша",
        color=0x10B981,
        description="Текущие параметры для этого канала. Изменение — текстом через "
                    "`кульш конфиг <параметр> <значение>`.",
    )
    embed.add_field(name="Язык", value=lang_disp, inline=True)
    embed.add_field(name="Тема", value=theme_disp, inline=True)
    embed.add_field(name="Модель", value=model_display_name(cfg.get("model")), inline=True)
    embed.add_field(name="Температура", value=str(cfg.get("temperature", 0.9)), inline=True)
    embed.add_field(name="Разбивка", value=sep, inline=True)
    embed.add_field(name="Стикеры/гифки", value=stickers, inline=True)
    embed.add_field(name="Автоответ", value=autoreply, inline=True)
    embed.add_field(name="Случайные сообщения", value=random_msgs, inline=True)
    embed.add_field(name="Серия (напоминание)", value=series, inline=True)
    embed.add_field(name="Кастомный промпт", value=prompt, inline=False)
    embed.add_field(
        name="Команды настройки",
        value=(
            "`кульш конфиг язык ru|en`\n"
            "`кульш конфиг тема тёмная|светлая`\n"
            "`кульш конфиг модель` — список\n"
            "`кульш конфиг модель <номер|авто>`\n"
            "`кульш конфиг температура <0.0-2.0>`\n"
            "`кульш конфиг разбивка вкл|выкл`\n"
            "`кульш конфиг стикеры вкл|выкл`\n"
            "`кульш конфиг автоответ вкл|выкл`\n"
            "`кульш конфиг рандом вкл|выкл`\n"
            "`кульш конфиг промпт <текст|сброс>`\n"
            "`кульш конфиг серия вкл|выкл`"
        ),
        inline=False,
    )
    return embed


async def ds_handle_config(message: discord.Message, user_id: int) -> None:
    chat_id = message.channel.id
    if message.guild and not message.author.guild_permissions.administrator:
        await message.reply("изменение настроек доступно только администраторам канала")
        return
    embed = _ds_config_embed(chat_id, user_id)
    await message.reply(embed=embed)


async def ds_handle_config_param(message: discord.Message, user_id: int, parts: list[str]) -> None:
    chat_id = message.channel.id
    if message.guild and not message.author.guild_permissions.administrator:
        await message.reply("изменение настроек доступно только администраторам канала")
        return
    cfg = get_user_config("ds", chat_id, user_id)
    if len(parts) < 3:
        await ds_handle_config(message, user_id)
        return
    param = parts[2].lower()
    val = parts[3].lower() if len(parts) >= 4 else ""
    bool_on = val in ("вкл", "on", "1", "true", "да")

    if param == "язык":
        if val in ("ru", "русский", "russian"):
            cfg["language"] = "ru"
            await message.reply("Язык: русский")
        elif val in ("en", "английский", "english"):
            cfg["language"] = "en"
            await message.reply("Language: English")
        else:
            await message.reply("Укажите `ru` или `en`.")
    elif param == "тема":
        if val in ("тёмная", "темная", "dark"):
            cfg["theme"] = "dark"
            await message.reply("Тема: тёмная")
        elif val in ("светлая", "light"):
            cfg["theme"] = "light"
            await message.reply("Тема: светлая")
        else:
            await message.reply("Укажите `тёмная` или `светлая`.")
    elif param == "серия":
        cfg["series_reminder_enabled"] = bool_on
        await message.reply("Напоминание о серии: " + ("вкл" if bool_on else "выкл"))
    elif param == "стикеры":
        cfg["stickers_enabled"] = bool_on
        await message.reply("Стикеры/гифки: " + ("вкл" if bool_on else "выкл"))
    elif param == "разбивка":
        cfg["separate_enabled"] = bool_on
        await message.reply("Разбивка на сообщения: " + ("вкл" if bool_on else "выкл"))
    elif param == "автоответ":
        cfg["random_reply_enabled"] = bool_on
        await message.reply("Автоответ: " + ("вкл" if bool_on else "выкл"))
    elif param == "рандом":
        cfg["random_messages_enabled"] = bool_on
        await message.reply("Случайные сообщения: " + ("вкл" if bool_on else "выкл"))
    elif param == "температура":
        try:
            t = max(0.0, min(2.0, float(val)))
            cfg["temperature"] = t
            await message.reply(f"Температура: {t}")
        except ValueError:
            await message.reply("Укажите число от 0.0 до 2.0.")
    elif param == "промпт":
        new_prompt = " ".join(parts[3:]).strip()
        if new_prompt.lower() in ("сброс", "убрать", "стандарт"):
            cfg["custom_prompt"] = None
            await message.reply("Промпт сброшен.")
        elif new_prompt:
            cfg["custom_prompt"] = new_prompt[:2000]
            await message.reply("Промпт установлен.")
        else:
            await message.reply("Введите текст или `сброс`.")
    elif param == "модель":
        if not val:
            lines = [f"`{i}` — {MODEL_DISPLAY.get(m, m)}" for i, m in enumerate(MODEL_LIST)]
            await message.reply(f"Текущая: {model_display_name(cfg.get('model'))}\n\n" + "\n".join(lines))
        elif val in ("авто", "auto"):
            cfg["model"] = None
            await message.reply("Модель: авто")
        else:
            try:
                idx = int(val)
                if 0 <= idx < len(MODEL_LIST):
                    cfg["model"] = MODEL_LIST[idx]
                    await message.reply(f"Модель: {MODEL_DISPLAY.get(MODEL_LIST[idx], MODEL_LIST[idx])}")
                else:
                    await message.reply("Неверный номер.")
            except ValueError:
                await message.reply("Введите номер или `авто`.")
    else:
        await message.reply("Неизвестный параметр. Используйте `кульш конфиг` для просмотра.")

# ============================================================
# DISCORD: SLASH-КОМАНДЫ
# ============================================================
def _ds_slash_help_text(lang: str) -> str:
    if lang == "ru":
        return (
            "# Кульш — команды\n\n"
            "**Основные**\n"
            "- `/start` — приветствие\n"
            "- `/menu` — интерактивное меню\n"
            "- `/help` — эта справка\n"
            "- `/donate` — поддержать проект\n"
            "- `/credits` — баланс кредитов\n\n"
            "**Настройки**\n"
            "- `/config` — текущие параметры канала\n"
            "Изменение: `кульш конфиг <параметр> <значение>`\n\n"
            "**Утилиты**\n"
            "- `/avatar` — описать аватарку\n"
            "- `/recall` — вспомнить последние медиа\n"
            "- `/logs` — логи сервера (админам)\n\n"
            "**Развлечения**\n"
            "- `/psl` — оценка внешности (looksmaxxing)\n"
            "- `/battle` — баттл двух фото\n\n"
            f"Веб-версия: {MINI_APP_URL}\n"
            f"GitHub: {GITHUB_URL}"
        )
    return (
        "# Kulsh — commands\n\n"
        "**Basics**\n"
        "- `/start` — greeting\n"
        "- `/menu` — interactive menu\n"
        "- `/help` — this help\n"
        "- `/donate` — support the project\n"
        "- `/credits` — credits balance\n\n"
        "**Settings**\n"
        "- `/config` — current channel settings\n"
        "Change: `kulsh config <param> <value>`\n\n"
        "**Tools**\n"
        "- `/avatar` — describe avatar\n"
        "- `/recall` — recall recent media\n"
        "- `/logs` — server logs (admins)\n\n"
        "**Entertainment**\n"
        "- `/psl` — looksmaxxing\n"
        "- `/battle` — two-photo battle\n\n"
        f"Web version: {MINI_APP_URL}\n"
        f"GitHub: {GITHUB_URL}"
    )


def _ds_slash_menu_text(lang: str) -> str:
    if lang == "ru":
        return (
            "# Меню Кульш AI\n\n"
            "Открытая языковая модель с набором встроенных инструментов. "
            "Ниже — основные разделы и команды.\n\n"
            "**Основные**\n"
            "- `/start` — приветствие\n"
            "- `/help` — полный список команд\n"
            "- `/config` — настройки канала\n"
            "- `/donate` — поддержка разработки\n"
            "- `/credits` — баланс кредитов\n\n"
            "**Инструменты**\n"
            "- `/avatar` — описать аватарку\n"
            "- `/recall` — вспомнить последние медиа\n"
            "- `/psl` — оценка внешности\n"
            "- `/battle` — баттл двух фото\n"
            "- `/logs` — логи сервера (админам)\n\n"
            f"Веб-версия: {MINI_APP_URL}"
        )
    return (
        "# Kulsh AI Menu\n\n"
        "An open-source language model with a set of built-in tools. "
        "Below are the main sections and commands.\n\n"
        "**Basics**\n"
        "- `/start` — greeting\n"
        "- `/help` — full command list\n"
        "- `/config` — channel settings\n"
        "- `/donate` — support development\n"
        "- `/credits` — credits balance\n\n"
        "**Tools**\n"
        "- `/avatar` — describe avatar\n"
        "- `/recall` — recall recent media\n"
        "- `/psl` — looksmaxxing\n"
        "- `/battle` — two-photo battle\n"
        "- `/logs` — server logs (admins)\n\n"
        f"Web version: {MINI_APP_URL}"
    )


def _ds_slash_start_text(lang: str) -> str:
    if lang == "ru":
        return (
            "# Кульш на связи\n\n"
            "Открытая языковая модель с анализом изображений, оценкой внешности "
            "и настройкой под себя. Работает в Telegram и Discord.\n\n"
            "**С чего начать**\n"
            "- `/menu` — все разделы\n"
            "- `/help` — список команд\n"
            "- `/config` — настройки канала\n\n"
            f"Веб-версия: {MINI_APP_URL}"
        )
    return (
        "# Kulsh is online\n\n"
        "An open-source language model with image analysis, looksmaxxing, "
        "and personal configuration. Available in Telegram and Discord.\n\n"
        "**Get started**\n"
        "- `/menu` — all sections\n"
        "- `/help` — command list\n"
        "- `/config` — channel settings\n\n"
        f"Web version: {MINI_APP_URL}"
    )


def _ds_lang_of(interaction: discord.Interaction) -> str:
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    cfg = get_user_config("ds", chat_id, user_id)
    return cfg.get("language", "ru")


@ds_tree.command(name="start", description="Greeting / Приветствие")
async def ds_slash_start(interaction: discord.Interaction):
    lang = _ds_lang_of(interaction)
    await interaction.response.send_message(_ds_slash_start_text(lang))


@ds_tree.command(name="menu", description="Menu / Меню")
async def ds_slash_menu(interaction: discord.Interaction):
    lang = _ds_lang_of(interaction)
    await interaction.response.send_message(_ds_slash_menu_text(lang))


@ds_tree.command(name="help", description="Command list / Список команд")
async def ds_slash_help(interaction: discord.Interaction):
    lang = _ds_lang_of(interaction)
    await interaction.response.send_message(_ds_slash_help_text(lang))


@ds_tree.command(name="donate", description="Support the project / Поддержать проект")
async def ds_slash_donate(interaction: discord.Interaction):
    lang = _ds_lang_of(interaction)
    if lang == "ru":
        text = (
            "# Поддержать Кульша\n\n"
            "Донаты идут на серверы, домены и дальнейшую разработку.\n\n"
            f"Онлайн-донат: {DONATE_URL}\n"
            f"GitHub: {GITHUB_URL}"
        )
    else:
        text = (
            "# Support Kulsh\n\n"
            "Donations go to servers, domains and further development.\n\n"
            f"Donate online: {DONATE_URL}\n"
            f"GitHub: {GITHUB_URL}"
        )
    await interaction.response.send_message(text)


@ds_tree.command(name="credits", description="Credits balance / Баланс кредитов")
async def ds_slash_credits(interaction: discord.Interaction):
    lang = _ds_lang_of(interaction)
    creds = get_user_credits("ds", interaction.user.id)
    if lang == "ru":
        await interaction.response.send_message(f"Кредиты: {creds}/{DAILY_CREDITS}")
    else:
        await interaction.response.send_message(f"Credits: {creds}/{DAILY_CREDITS}")


@ds_tree.command(name="config", description="Channel settings / Настройки канала")
async def ds_slash_config(interaction: discord.Interaction):
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    if interaction.guild and not interaction.user.guild_permissions.administrator:
        lang = _ds_lang_of(interaction)
        msg = "изменение настроек доступно только администраторам канала" if lang == "ru" \
            else "only channel administrators can change settings"
        await interaction.response.send_message(msg, ephemeral=True)
        return
    embed = _ds_config_embed(chat_id, user_id)
    await interaction.response.send_message(embed=embed)


@ds_tree.command(name="avatar", description="Describe avatar / Описать аватарку")
@app_commands.describe(user="Whose avatar to describe / Чью аватарку описать")
async def ds_slash_avatar(interaction: discord.Interaction, user: discord.Member | None = None):
    await interaction.response.defer()
    target = user or interaction.user
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    try:
        img_bytes = await download_image_bytes(target.display_avatar.url)
        raw = await ask_ai_async(
            prompt=(f"Ты только что посмотрел аватарку пользователя {target.display_name}. "
                    f"Опиши коротко (1-2 предложения) в стиле Кульша. Без markdown. "
                    f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif."),
            image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id, platform="ds",
        )
        segments = clean_extra_text(raw) if raw else []
        if not segments:
            await interaction.followup.send("не удалось получить описание")
            return
        for seg in segments:
            await interaction.followup.send(seg)
    except Exception as e:
        logger.error(f"DS slash avatar: {e}")
        await interaction.followup.send(f"Ошибка: {e}")


@ds_tree.command(name="recall", description="Recall recent media / Вспомнить недавние медиа")
@app_commands.describe(count="How many last items / Сколько последних элементов")
async def ds_slash_recall(interaction: discord.Interaction, count: int = 3):
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    n = max(1, min(10, count))
    history = list(chat_media_history.get(f"ds_{chat_id}", []))
    if not history:
        await interaction.followup.send("в памяти нет медиа")
        return
    last = history[-n:]
    lines = [f"- {it.get('type', 'media')} от {it.get('sender', '?')}: {(it.get('caption') or '')[:120]}"
             for it in last]
    meta = "\n".join(lines)
    try:
        raw = await ask_ai_async(
            prompt=(f"Ты вспоминаешь недавние медиа. Список:\n{meta}\n\n"
                    f"Коротко прокомментируй в стиле Кульша. Без markdown. "
                    f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif."),
            chat_id=chat_id, user_id=user_id, platform="ds",
        )
        segments = clean_extra_text(raw) if raw else []
        if not segments:
            await interaction.followup.send(meta)
            return
        for seg in segments:
            await interaction.followup.send(seg)
    except Exception as e:
        logger.error(f"DS slash recall: {e}")
        await interaction.followup.send(f"Ошибка: {e}")


@ds_tree.command(name="logs", description="Server logs (admins) / Логи сервера (админам)")
async def ds_slash_logs(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.id not in AUTHORIZED_UPDATERS:
        await interaction.followup.send("недостаточно прав", ephemeral=True)
        return
    try:
        tail = read_log_tail(20)
        content = f"{LOG_INTRO}\n```\n{tail}\n```" if len(tail) <= 1900 else f"{LOG_INTRO}\n\n{tail[:1900]}"
        try:
            await interaction.followup.send(content=content, file=discord.File('bot.log'), ephemeral=True)
        except FileNotFoundError:
            await interaction.followup.send(content=content, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}", ephemeral=True)


@ds_tree.command(name="psl", description="Looksmaxxing analysis / Оценка внешности")
@app_commands.describe(image="Photo / Фото", advice="Include advice / Показать рекомендации")
async def ds_slash_psl(interaction: discord.Interaction, image: discord.Attachment, advice: bool = False):
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    try:
        img_bytes = await download_image_bytes(image.url)
        cfg = get_user_config("ds", chat_id, user_id)
        lang = cfg.get("language", "ru")
        theme = cfg.get("theme", "dark")
        ai_data = await get_looksmaxxing_data(img_bytes, advice, lang=lang)
        if "error" in ai_data:
            await interaction.followup.send(f"Ошибка: {ai_data['error']}")
            return
        infographic = await create_infographic(img_bytes, ai_data, theme=theme, lang=lang)
        if lang == "ru":
            report = (
                f"**LOOKSMAXXING**\n"
                f"Пол: {ai_data.get('gender', '?')}\n"
                f"PSL: `{ai_data.get('psl', '?')}/8.0`\n"
                f"Tier: `{ai_data.get('tier', '?')}`\n"
            )
            if ai_data.get("potential"):
                report += f"Потенциал: `{ai_data['potential']}`\n"
            report += f"\n{ai_data.get('summary', '')}"
            if advice and ai_data.get("advice"):
                report += f"\n\n**Рекомендации:**\n{ai_data['advice']}"
        else:
            report = (
                f"**LOOKSMAXXING**\n"
                f"Gender: {ai_data.get('gender', '?')}\n"
                f"PSL: `{ai_data.get('psl', '?')}/8.0`\n"
                f"Tier: `{ai_data.get('tier', '?')}`\n"
            )
            if ai_data.get("potential"):
                report += f"Potential: `{ai_data['potential']}`\n"
            report += f"\n{ai_data.get('summary', '')}"
            if advice and ai_data.get("advice"):
                report += f"\n\n**Advice:**\n{ai_data['advice']}"
        await interaction.followup.send(
            content=report[:1900],
            file=discord.File(fp=infographic, filename="psl.png"),
        )
        if len(report) > 1900:
            await interaction.followup.send(report[1900:])
    except Exception as e:
        logger.error(f"DS slash psl: {e}")
        await interaction.followup.send(f"Ошибка: {e}")


@ds_tree.command(name="battle", description="Two-photo battle / Баттл двух фото")
@app_commands.describe(image1="First photo / Первое фото", image2="Second photo / Второе фото")
async def ds_slash_battle(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment):
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    try:
        p1 = await download_image_bytes(image1.url)
        p2 = await download_image_bytes(image2.url)
        cfg = get_user_config("ds", chat_id, user_id)
        lang = cfg.get("language", "ru")
        theme = cfg.get("theme", "dark")
        ai_data = await get_battle_data(p1, p2, lang=lang)
        if "error" in ai_data:
            await interaction.followup.send(f"Ошибка: {ai_data['error']}")
            return
        img = await create_battle_infographic(p1, p2, ai_data, theme=theme, lang=lang)
        winner_num = str(ai_data.get("winner", "1"))
        if lang == "ru":
            winner_label = "Первое фото" if winner_num == "1" else "Второе фото"
            report = (
                f"**РЕЗУЛЬТАТ БАТТЛА**\n\n"
                f"Победитель: **{winner_label}**\n"
                f"Причина: {ai_data.get('reason', '')}\n\n"
                f"Фото 1: PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
                f"{ai_data.get('photo1', {}).get('tier', '?')}\n"
                f"Фото 2: PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
                f"{ai_data.get('photo2', {}).get('tier', '?')}"
            )
        else:
            winner_label = "First photo" if winner_num == "1" else "Second photo"
            report = (
                f"**BATTLE RESULT**\n\n"
                f"Winner: **{winner_label}**\n"
                f"Reason: {ai_data.get('reason', '')}\n\n"
                f"Photo 1: PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
                f"{ai_data.get('photo1', {}).get('tier', '?')}\n"
                f"Photo 2: PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
                f"{ai_data.get('photo2', {}).get('tier', '?')}"
            )
        await interaction.followup.send(
            content=report[:1900],
            file=discord.File(fp=img, filename="battle.png"),
        )
    except Exception as e:
        logger.error(f"DS slash battle: {e}")
        await interaction.followup.send(f"Ошибка: {e}")

# ============================================================
# DISCORD: MESSAGE HANDLER
# ============================================================
@ds_bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == ds_bot.user or message.author.bot:
        return
    is_dm = message.guild is None
    chat_id = message.author.id if is_dm else message.guild.id
    user_id = message.author.id
    content_lower = message.content.lower()
    display_name = getattr(message.author, "display_name", message.author.name)
    username = message.author.name

    if not is_dm and content_lower.startswith("кульш обновись"):
        if message.author.id not in AUTHORIZED_UPDATERS:
            await message.reply("недостаточно прав")
            return
        await message.reply("обновляюсь с автооткатом при ошибке...")
        try:
            repo_path = os.getenv('REPO_PATH', os.getcwd())
            status, info = await perform_safe_git_update(repo_path)
            if status == "up_to_date":
                await message.reply(f"уже актуальная версия:\n```\n{info[:1500]}\n```")
            elif status == "ok":
                await message.reply(f"изменения подтянуты, перезапускаюсь:\n```\n{info[:1500]}\n```")
                await asyncio.sleep(2)
                os._exit(0)
            elif status == "rolled_back":
                await message.reply(
                    "новый коммит содержит ошибки — откатился к предыдущей версии. "
                    "Бот продолжает работу.\n"
                    f"```\n{info[:1500]}\n```"
                )
            else:
                await message.reply(f"ошибка обновления:\n```\n{info[:1500]}\n```")
        except Exception as e:
            logger.exception("update error")
            await message.reply(f"ошибка обновления:\n```\n{e}\n```")
        return

    if content_lower.startswith("кульш конфиг") or content_lower.startswith("кульш настройки"):
        parts = message.content.split()
        if len(parts) == 2:
            await ds_handle_config(message, user_id)
        else:
            await ds_handle_config_param(message, user_id, parts)
        return

    if content_lower.startswith("кульш донаты"):
        top = get_top_donators()
        if not top:
            await message.reply(f"Пока никто не донатил.\n{DONATE_URL}")
            return
        embed = discord.Embed(title="Топ донатеров", color=0x10B981)
        for i, (name, total) in enumerate(top, 1):
            embed.add_field(name=f"{i}. {name}", value=f"{total} очков", inline=False)
        await message.reply(embed=embed)
        return

    if content_lower.startswith("кульш аватарк") or content_lower.startswith("кульш аватар"):
        raw = await get_avatar_description_ds(message, chat_id, user_id)
        if not raw:
            await message.reply("не удалось получить аватарку")
            return
        for seg in clean_extra_text(raw):
            try:
                await message.channel.send(seg)
            except Exception as e:
                logger.warning(f"DS avatar: {e}")
        return

    if not is_dm and "кульш логи" in content_lower:
        if message.author.id not in AUTHORIZED_UPDATERS:
            await message.reply("недостаточно прав")
            return
        try:
            tail = read_log_tail(20)
            try:
                await message.reply(
                    content=f"{LOG_INTRO}\n```\n{tail}\n```" if len(tail) <= 1900 else LOG_INTRO,
                    file=discord.File('bot.log'),
                )
            except FileNotFoundError:
                await message.reply(
                    f"{LOG_INTRO}\n```\n{tail}\n```" if len(tail) <= 1900 else f"{LOG_INTRO}\n\n{tail}"
                )
                return
            if len(tail) > 1900:
                for chunk in chunk_text(tail, 1900):
                    await message.channel.send(f"```\n{chunk}\n```")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")
        return

    if not is_dm and "кульш зайди в войс" in content_lower:
        author = cast(discord.Member, message.author)
        if not (author.voice and author.voice.channel):
            await message.reply("вы не в голосовом канале")
            return
        voice_channel = author.voice.channel
        try:
            vc = cast(discord.VoiceChannel, message.guild.voice_client)
            if vc and vc.is_connected():
                await vc.move_to(voice_channel)
            else:
                if VOICE_RECOGNITION_ENABLED and VOICE_RECV_AVAILABLE:
                    vc = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
                else:
                    vc = await voice_channel.connect()
            voice_text_channels[message.guild.id] = message.channel
            await message.reply(f"подключился к {voice_channel.name}")
            if VOICE_RECOGNITION_ENABLED and VOICE_RECV_AVAILABLE:
                sink = RecognitionSink(ds_bot, message.guild, message.channel)
                vc.listen(sink)
                setattr(vc, "_recognition_sink", sink)
        except Exception as e:
            logger.error(f"voice: {e}")
            await message.reply("не удалось подключиться.")
        return

    if not is_dm and "кульш выйди из войса" in content_lower:
        vc = cast(discord.VoiceChannel, message.guild.voice_client)
        if vc and vc.is_connected():
            if hasattr(vc, "_recognition_sink"):
                getattr(vc, "_recognition_sink").cleanup()
            await vc.disconnect()
            voice_text_channels.pop(message.guild.id, None)
            await message.reply("отключился")
        else:
            await message.reply("я и так не в голосовом")
        return

    if is_looksmaxxing_command(message.content) and len(message.attachments) == 0:
        add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                        message.content, message_id=message.id)
        await message.reply("Пришлите фото с командой `кульш psl` или используйте `/psl`.")
        return

    if is_battle_command(message.content) and len(message.attachments) == 0:
        add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                        message.content, message_id=message.id)
        await message.reply("Для баттла пришлите два фото или используйте `/battle`.")
        return

    image_attachments = [a for a in message.attachments if a.content_type and a.content_type.startswith('image/')]
    video_attachments = [a for a in message.attachments if a.content_type and a.content_type.startswith('video/')]
    has_battle_cmd = is_battle_command(message.content)

    if has_battle_cmd and len(image_attachments) >= 2:
        async with message.channel.typing():
            status = await message.reply("сравниваю...")
            try:
                p1 = await download_image_bytes(image_attachments[0].url)
                p2 = await download_image_bytes(image_attachments[1].url)
                cfg = get_user_config("ds", chat_id, user_id)
                lang = cfg.get("language", "ru")
                theme = cfg.get("theme", "dark")
                ai_data = await get_battle_data(p1, p2, lang=lang)
                if "error" in ai_data:
                    await status.edit(content=f"Ошибка: {ai_data['error']}")
                    return
                img = await create_battle_infographic(p1, p2, ai_data, theme=theme, lang=lang)
                winner_num = str(ai_data.get("winner", "1"))
                winner_label = "Первое фото" if winner_num == "1" else "Второе фото"
                report = (
                    f"**РЕЗУЛЬТАТ БАТТЛА**\n\n"
                    f"Победитель: **{winner_label}**\n"
                    f"Причина: {ai_data.get('reason', '')}\n\n"
                    f"Фото 1: PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
                    f"{ai_data.get('photo1', {}).get('tier', '?')}\n"
                    f"Фото 2: PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
                    f"{ai_data.get('photo2', {}).get('tier', '?')}"
                )
                await message.reply(file=discord.File(fp=img, filename="battle.png"),
                                    content=report[:1900])
                await status.delete()
                add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                                "[battle]", message_id=message.id)
                add_bot_memory(f"ds_{chat_id}", "[battle результат]")
            except Exception as e:
                logger.error(f"DS battle: {e}")
                await status.edit(content=f"Ошибка: {e}")
        return

    has_looksmaxxing_cmd = is_looksmaxxing_command(message.content)
    if has_looksmaxxing_cmd and len(image_attachments) > 0:
        async with message.channel.typing():
            try:
                img_bytes = await download_image_bytes(image_attachments[0].url)
                include_advice = "совет" in content_lower or "advice" in content_lower
                cfg = get_user_config("ds", chat_id, user_id)
                lang = cfg.get("language", "ru")
                theme = cfg.get("theme", "dark")
                ai_data = await get_looksmaxxing_data(img_bytes, include_advice, lang=lang)
                if "error" in ai_data:
                    await message.reply(f"Ошибка: {ai_data['error']}")
                    return
                infographic = await create_infographic(img_bytes, ai_data, theme=theme, lang=lang)
                report = (
                    f"**LOOKSMAXXING**\n"
                    f"Пол: {ai_data.get('gender', '?')}\n"
                    f"PSL: `{ai_data.get('psl', '?')}/8.0`\n"
                    f"Tier: `{ai_data.get('tier', '?')}`\n"
                )
                if ai_data.get("potential"):
                    report += f"Потенциал: `{ai_data['potential']}`\n"
                report += f"\n{ai_data.get('summary', '')}"
                if include_advice and ai_data.get("advice"):
                    report += f"\n\n**Рекомендации:**\n{ai_data['advice']}"
                await message.reply(file=discord.File(fp=infographic, filename="psl.png"),
                                    content=report[:1900])
                if len(report) > 1900:
                    await message.channel.send(report[1900:])
            except Exception as e:
                logger.error(f"DS looksmaxxing: {e}")
                await message.reply(f"Ошибка: {e}")
        return

    for att in image_attachments:
        add_media_history(f"ds_{chat_id}", att.url, "photo", display_name, caption=message.content[:200])
    for att in video_attachments:
        add_media_history(f"ds_{chat_id}", att.url, "video", display_name, caption=message.content[:200])

    is_reply_to_bot = False
    if message.reference and message.reference.resolved and isinstance(message.reference.resolved, discord.Message):
        if message.reference.resolved.author == ds_bot.user:
            is_reply_to_bot = True

    addressed = bool(is_reply_to_bot or re.search(r'(?i)\bкульш\b', message.content) or is_dm)

    if (image_attachments or video_attachments) and addressed:
        async with message.channel.typing():
            try:
                img_bytes = None
                img_mime = "image/jpeg"
                if image_attachments:
                    img_bytes = await download_image_bytes(image_attachments[0].url)
                    img_mime = image_attachments[0].content_type or "image/jpeg"
                elif video_attachments:
                    vid = await download_image_bytes(video_attachments[0].url)
                    frame = await extract_video_frame(vid, ".mp4")
                    if frame:
                        img_bytes = frame
                prompt = message.content.strip() or "что на этом?"
                add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                                f"{prompt} [с медиа]",
                                ["photo" if image_attachments else "video"],
                                message_id=message.id)
                messages = memory_to_messages(get_chat_memory(f"ds_{chat_id}"))
                answer = await ask_ai_async(messages=messages, image_bytes=img_bytes,
                                            image_mime=img_mime, chat_id=chat_id,
                                            user_id=user_id, platform="ds")
                await send_ds_ai_response(message, chat_id, user_id, answer)
                asyncio.create_task(extract_memory(f"ds_{chat_id}", f"{display_name}: [медиа]", answer))
            except Exception as e:
                logger.info(f"DS media: {e}")
                await message.reply("не удалось обработать вложение")
        return

    if addressed:
        async with message.channel.typing():
            add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                            message.content, message_id=message.id)
            messages = memory_to_messages(get_chat_memory(f"ds_{chat_id}"))
            answer = await ask_ai_async(messages=messages, chat_id=chat_id,
                                        user_id=user_id, platform="ds")
            await send_ds_ai_response(message, chat_id, user_id, answer)
            asyncio.create_task(extract_memory(f"ds_{chat_id}", f"{display_name}: {message.content}", answer))
        return

    add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                    message.content, message_id=message.id)
    if await should_random_reply("ds", chat_id, user_id):
        try:
            answer = await ask_ai_async(
                context_type="observer",
                messages=memory_to_messages(get_chat_memory(f"ds_{chat_id}")),
                chat_id=chat_id, user_id=user_id, platform="ds",
            )
            if answer and answer.strip() and answer.strip().upper() != "НЕТ":
                last_random_reply[f"ds_{chat_id}"] = time.time()
                await send_ds_ai_response(message, chat_id, user_id, answer)
        except Exception as e:
            logger.warning(f"DS random reply: {e}")

# ============================================================
# DONATION ALERTS
# ============================================================
async def send_donation_alert(platform: str, name: str, amount: int, message_text: str = '') -> None:
    if platform == 'tg':
        text = f"{name} задонатил {amount} звёзд. Спасибо за поддержку."
        if message_text:
            text += f"\nСообщение: {message_text}"
        try:
            await send_tg_html(TG_TARGET_CHAT, text)
        except Exception as e:
            logger.error(f"Донат в ТГ: {e}")
    elif platform == 'ds':
        text = f"{name} задонатил {amount} руб."
        if message_text:
            text += f"\n> {message_text}"
        if DS_DONATION_CHANNEL_ID:
            channel = ds_bot.get_channel(DS_DONATION_CHANNEL_ID)
            if channel:
                try:
                    await channel.send(text)
                except Exception as e:
                    logger.error(f"Донат в DS: {e}")


async def donation_alerts_listener() -> None:
    if not DONATIONALERTS_TOKEN:
        logger.info("DonationAlerts токен не задан.")
        return
    await ds_bot.wait_until_ready()
    sio = socketio.AsyncClient(query={'token': DONATIONALERTS_TOKEN})

    @sio.event
    async def connect() -> None:
        logger.info("DonationAlerts подключён")

    @sio.event
    async def disconnect() -> None:
        logger.warning("DonationAlerts отключён")

    @sio.on('donation')
    async def on_donation(data: dict) -> None:
        try:
            amount = float(data.get('amount', 0))
            currency = data.get('currency', 'RUB')
            if currency != 'RUB':
                return
            points = int(amount)
            username = data.get('username', 'Аноним')
            message = data.get('message', '')
            logger.info(f"Донат {username} → {points}")
            add_donation('ds', 0, points, name=username)
            await send_donation_alert('ds', username, points, message)
        except Exception as e:
            logger.error(f"DA error: {e}")

    try:
        await sio.connect('https://socket.donationalerts.ru:443',
                          transports=['websocket'], ssl_verify=False)
        await sio.wait()
    except Exception as e:
        logger.error(f"DA connect fail: {e}")

# ============================================================
# VOICE SINK
# ============================================================
if VOICE_RECOGNITION_ENABLED and VOICE_RECV_AVAILABLE:
    class RecognitionSink(voice_recv.AudioSink):
        def __init__(self, bot, guild, text_channel):
            super().__init__()
            self.bot = bot
            self.guild = guild
            self.text_channel = text_channel
            self.buffers = {}
            self.recognizer = sr.Recognizer()
            self.processing_tasks = {}

        def wants_opus(self) -> bool:
            return False

        def write(self, user, data):
            user_id = user.id if user else "unknown_session"
            user_name = user.name if user else "Аноним"
            if user and user.bot:
                return
            if user_id not in self.buffers:
                self.buffers[user_id] = bytearray()
            self.buffers[user_id].extend(data.pcm)
            if len(self.buffers[user_id]) > 380000:
                if user_id in self.processing_tasks:
                    self.processing_tasks[user_id].cancel()
                self.processing_tasks[user_id] = asyncio.run_coroutine_threadsafe(
                    self.wait_and_process(user_id, user_name), self.bot.loop
                )

        def _sync_recognize(self, pcm_data):
            try:
                audio = AudioSegment(data=pcm_data, sample_width=2, frame_rate=48000,
                                     channels=2).set_channels(1).set_frame_rate(16000)
                wav_io = BytesIO()
                audio.export(wav_io, format="wav")
                wav_io.seek(0)
                with sr.AudioFile(wav_io) as source:
                    return self.recognizer.recognize_google(
                        self.recognizer.record(source), language="ru-RU"
                    )
            except sr.UnknownValueError:
                return None
            except Exception as e:
                logger.error(f"recognize: {e}")
                return None

        async def wait_and_process(self, user_id, user_name):
            try:
                await asyncio.sleep(1.5)
                if user_id in self.buffers:
                    pcm_data = bytes(self.buffers.pop(user_id))
                    text = await asyncio.to_thread(self._sync_recognize, pcm_data)
                    if text and random.random() <= 0.65:
                        logger.info(f"Распознано: {text}")
            except asyncio.CancelledError:
                pass

        def cleanup(self):
            for task in self.processing_tasks.values():
                task.cancel()
            self.buffers.clear()
else:
    class RecognitionSink:
        pass

# ============================================================
# TTS
# ============================================================
async def say_in_voice(voice_client, text):
    if not VOICE_ENABLED or not voice_client or not voice_client.is_connected():
        return
    try:
        filename = f"temp_voice_{voice_client.guild.id}.mp3"
        communicate = edge_tts.Communicate(text, "uk-UA-OstapNeural")
        await communicate.save(filename)
        if voice_client.is_playing():
            voice_client.stop()
        voice_client.play(discord.FFmpegPCMAudio(filename))
    except Exception as e:
        logger.error(f"TTS: {e}")

# ============================================================
# LOOPS
# ============================================================
async def random_post_loop() -> None:
    while True:
        await asyncio.sleep(random.randint(3600, 14400))
        chat_key = f"tg_{TG_TARGET_CHAT}"
        memory = get_chat_memory(chat_key)
        try:
            if memory:
                answer = await ask_ai_async(
                    prompt=("Посмотри на историю чата. Если хочешь что-то добавить или пошутить, напиши одно "
                            "короткое сообщение. Если нет — ответь ровно 'НЕТ'."),
                    context_type="observer",
                    messages=memory_to_messages(memory),
                    chat_id=TG_TARGET_CHAT, user_id=0, platform="tg",
                )
            else:
                answer = await ask_ai_async(prompt=None, context_type="random",
                                            chat_id=TG_TARGET_CHAT, user_id=0, platform="tg")
            if not answer or not answer.strip() or answer.strip().upper() == "НЕТ":
                continue
            segments, markers = process_ai_response(answer, separate_enabled=True)
            for seg in segments:
                await send_tg_html(TG_TARGET_CHAT, seg)
                add_bot_memory(chat_key, seg)
            for m in markers:
                if m == "sticker":
                    try:
                        await tg_bot.send_sticker(TG_TARGET_CHAT, random.choice(STICKER_POOL))
                    except Exception as e:
                        logger.warning(f"random_post sticker: {e}")
        except Exception as e:
            logger.info(f"random_post_loop: {e}")


async def series_reminder_loop() -> None:
    await ds_bot.wait_until_ready()
    channel = cast(discord.TextChannel, ds_bot.get_channel(DS_SERIES_CHANNEL_ID))
    if not channel:
        logger.error("Канал серии не найден")
        return
    while True:
        try:
            prompt = ("Попроси Антона отправить Фолзу сообщение в TikTok, чтобы продлить серию. "
                      "Одно короткое сообщение в стиле Кульша.")
            answer = await ask_ai_async(prompt=prompt, context_type="default",
                                        chat_id=DS_SERIES_CHANNEL_ID, user_id=0, platform="ds")
            segments, _ = process_ai_response(answer, separate_enabled=True)
            if segments:
                await channel.send(f"<@{DS_SERIES_TARGET_USER_ID}> {segments[0]}")
                for seg in segments[1:]:
                    await channel.send(seg)
        except Exception as e:
            logger.error(f"series_reminder_loop: {e}")
        await asyncio.sleep(86400)

# ============================================================
# ЗАПУСК
# ============================================================
async def main() -> None:
    asyncio.create_task(random_post_loop())

    @ds_bot.event
    async def on_ready() -> None:
        logger.info(f'Discord {ds_bot.user} запущен, discord.py {discord.__version__}')
        if not VOICE_RECOGNITION_ENABLED:
            logger.info("Распознавание голоса отключено")

        # Синхронизация slash-команд с гильдией
        try:
            guild = discord.Object(id=DS_ALLOWED_GUILD_ID)
            ds_tree.copy_global_to(guild=guild)
            synced = await ds_tree.sync(guild=guild)
            logger.info(f"Синхронизировано slash-команд: {len(synced)}")
        except Exception as e:
            logger.error(f"Не удалось синхронизировать slash-команды: {e}")

        asyncio.create_task(series_reminder_loop())
        if DONATIONALERTS_TOKEN:
            asyncio.create_task(donation_alerts_listener())

    async def start_discord() -> None:
        await ds_bot.start(DISCORD_TOKEN)

    async def start_telegram() -> None:
        await tg_bot.polling(non_stop=True)

    await asyncio.gather(start_discord(), start_telegram())


if __name__ == "__main__":
    logger.info(f">>> Кульш в эфире. МСК: {msk_datetime_str()}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
