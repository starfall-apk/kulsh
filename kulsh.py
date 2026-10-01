# Kulsh GPT | v2.39.0 (no GIFs in menu/start, restored start emojis, centered KULSH table,
# slower apply animation, decorative unicode design, web search without API keys,
# full Pillow-based infographic engine (bar/line/pie/3d_pie/table/text/images/themes))
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
from typing import Any, Callable, Protocol, TypeAlias, TypeVar, cast
from urllib.parse import quote_plus, unquote, urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
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
TG_TOKEN: str = os.getenv('TG_TOKEN') or ""
DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN') or ""
AI_KEY = os.getenv('AI_KEY')
AI_KEY_1 = os.getenv('AI_KEY_1')
AI_KEY_2 = os.getenv('AI_KEY_2')
AI_KEY_3 = os.getenv('AI_KEY_3')
TG_TARGET_CHAT = int(os.getenv('TG_TARGET_CHAT') or "0")
DS_ALLOWED_GUILD_ID = int(os.getenv('DS_ALLOWED_GUILD_ID') or "0")
DS_DONATION_CHANNEL_ID = int(os.getenv('DONATIONALERTS_CHANNEL_ID', '0'))
DONATIONALERTS_TOKEN = os.getenv('DONATIONALERTS_TOKEN', '')

AI_KEYS = [k for k in [AI_KEY_1, AI_KEY_2, AI_KEY_3] if k]
if not AI_KEYS and AI_KEY:
    AI_KEYS.append(AI_KEY)
if not AI_KEYS:
    logger.critical("❌ Не найден ни один API ключ Gemini!")
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
DONATE_URL = "https://kulsh.vercel.app/donate"
GITHUB_URL = "https://github.com/starfall-apk/kulsh"

MODEL_LIST = [
    "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash",
    "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash",
    "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest",
    "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview",
]
MODEL_DISPLAY: dict[str, str] = {
    "gemini-3.8-flash": "🚀 3.8 Flash",
    "gemini-3.7-flash": "⚡ 3.7 Flash",
    "gemini-3.6-flash": "🌠 3.6 Flash",
    "gemini-3.5-flash": "💫 3.5 Flash",
    "gemini-3.5-flash-lite": "✨ 3.5 Flash Lite",
    "gemini-2.5-flash": "🌟 2.5 Flash",
    "gemini-2.5-flash-lite": "💡 2.5 Flash Lite",
    "gemini-flash-latest": "🔥 Flash Latest",
    "gemini-flash-lite-latest": "🌱 Flash Lite Latest",
    "gemini-3-flash-preview": "🧪 3 Flash Preview",
    "gemini-3.1-flash-lite-preview": "🧬 3.1 Flash Lite Preview",
}


def model_display_name(model: str | None, lang: str = "ru") -> str:
    if not model:
        return "🎲 авто (все подряд)" if lang == "ru" else "🎲 auto (all models)"
    return MODEL_DISPLAY.get(model, model)


LOG_INTRO = "🍷🗿 Вот логи сервера, босс:"
PREMIUM_ADMIN_ID = 1420898868
premium_functions_enabled: bool = True
AUTHORIZED_UPDATERS = [735217033867821098, 1193627300797878362]

# Декоративные символы для красивого оформления
DECO = {
    "sparkle": "✦",
    "wave": "彡",
    "rivers": "巛",
    "stroke": "〢",
    "line": "─",
    "dline": "═",
    "dot": "▪",
    "hollow": "▫",
    "arrow": "▸",
    "diamond": "◈",
    "star": "★",
    "star_hollow": "☆",
    "flower": "❋",
    "dash": "─",
    "bul": "•",
}


def deco_divider(length: int = 20, char: str = "─") -> str:
    return char * length


def deco_title(text: str, lang: str = "ru") -> str:
    return f"✦彡巛〢 {text} 〢巛彡✦"


# ============================================================
# ЛОКАЛИЗАЦИЯ
# ============================================================
TEXTS: dict[str, tuple[str, str]] = {
    "cfg_title":               ("⚙️ Настройки", "⚙️ Settings"),
    "cfg_lang":                ("🌐 Язык", "🌐 Language"),
    "cfg_theme":               ("🌓 Тема", "🌓 Theme"),
    "cfg_model":               ("🧠 Модель", "🧠 Model"),
    "cfg_temp_short":          ("🎛 Темп.", "🎛 Temp"),
    "cfg_sep":                 ("💬 Разбивка", "💬 Split"),
    "cfg_stream":              ("📡 Стриминг", "📡 Streaming"),
    "cfg_stickers":            ("🎨 Стикеры", "🎨 Stickers"),
    "cfg_autoreply":           ("🗣 Автоотв.", "🗣 Auto-reply"),
    "cfg_random":              ("📢 Рандом", "📢 Random"),
    "cfg_websearch":           ("🔎 Веб-поиск", "🔎 Web search"),
    "cfg_edit_prompt":         ("📝 Изменить промпт", "📝 Edit prompt"),
    "cfg_reset_memory":        ("🧹 Сбросить память", "🧹 Reset memory"),
    "cfg_reset_prompt":        ("♻️ Сбросить промпт", "♻️ Reset prompt"),
    "cfg_apply_close":         ("✅ Применить и закрыть", "✅ Apply & close"),
    "cfg_back":                ("🔙 Назад", "🔙 Back"),
    "cfg_back_slash":          ("🔙 Назад / Back", "🔙 Back"),
    "cfg_auto":                ("🎲 Авто", "🎲 Auto"),
    "cfg_choose_model":        ("🧠 Выбор модели", "🧠 Model selection"),
    "cfg_current":             ("Текущая", "Current"),
    "cfg_auto_hint":           ("перебор всех моделей", "try all models"),
    "cfg_prompt_label":        ("📝 Кастомный промпт", "📝 Custom prompt"),
    "cfg_prompt_default":      ("стандартный", "default"),
    "cfg_credits_label":       ("💎 Кредиты", "💎 Credits"),

    "cfg_updated":             ("Обновлено", "Updated"),
    "cfg_model_auto":          ("Модель: авто", "Model: auto"),
    "cfg_model_set":           ("Модель: {0}", "Model: {0}"),
    "cfg_lang_set_ru":         ("Язык: русский 🇷🇺", "Language: Russian 🇷🇺"),
    "cfg_lang_set_en":         ("Язык: английский 🇬🇧", "Language: English 🇬🇧"),
    "cfg_theme_dark":          ("Тема: тёмная 🌑", "Theme: dark 🌑"),
    "cfg_theme_light":         ("Тема: светлая ☀️", "Theme: light ☀️"),
    "cfg_temp":                ("🌡 {0}", "🌡 {0}"),
    "cfg_prompt_reset":        ("Промпт сброшен", "Prompt reset"),
    "cfg_memory_reset":        ("Память сброшена", "Memory reset"),
    "cfg_done":                ("Готово ✅", "Done ✅"),
    "cfg_mutex": (
        "«Разбивка» и «Стриминг» взаимно исключаемы. Сначала отключи вторую настройку.",
        "Split and Streaming are mutually exclusive. Disable the other first.",
    ),
    "cfg_premium_off":         ("расширенные функции отключены", "extended features disabled"),
    "cfg_not_yours":           ("это не твои настройки 🤚", "not your settings 🤚"),
    "cfg_edit_prompt_ask": (
        "Отправьте новый кастомный промпт ответом на это сообщение.\n"
        "Для отмены — ответьте <code>отмена</code> или <code>cancel</code>.",
        "Send the new custom prompt as a reply to this message.\n"
        "To cancel — reply <code>отмена</code> or <code>cancel</code>.",
    ),
    "prompt_saved":            ("Промпт сохранён ({0} символов)", "Prompt saved ({0} chars)"),
    "prompt_cancelled":        ("Изменение промпта отменено", "Prompt edit cancelled"),

    # ---- МЕНЮ (без гif) ----
    "menu_title":              ("Кульш AI — главное меню", "Kulsh AI — Main Menu"),
    "menu_intro": (
        "Открытая языковая модель с набором встроенных инструментов, "
        "веб-поиском и генерацией инфографики.",
        "Open-source language model with built-in tools, web search and infographic generation.",
    ),
    "menu_available":          ("Доступно:", "Available:"),
    "menu_mini_app":           ("Mini App — расширенный чат с ИИ",
                                "Mini App — extended AI chat"),
    "menu_settings_item":      ("Настройки — язык, тема, модель, промпт, поиск",
                                "Settings — language, theme, model, prompt, search"),
    "menu_commands":           ("Команды — полный список возможностей",
                                "Commands — full feature list"),
    "menu_donate_item":        ("Донат — поддержка разработки", "Donate — support development"),
    "menu_github_item":        ("GitHub — исходный код проекта", "GitHub — project source code"),

    # ---- START (с эмодзи как в оригинале) ----
    "start_title":             ("🍷🗿 Кульш на связи", "🍷🗿 Kulsh is online"),
    "start_intro": (
        "Открытая языковая модель с анализом изображений, веб-поиском, "
        "генерацией инфографики и настройкой под себя. Telegram и Discord.",
        "Open-source language model with image analysis, web search, "
        "infographic generation and personal config. Telegram and Discord.",
    ),
    "start_where":             ("🚀 С чего начать:", "🚀 Where to start:"),
    "start_mini_app":          ("🚀 Mini App — расширенный чат с ИИ",
                                "🚀 Mini App — extended AI chat"),
    "start_menu":              ("📖 Меню — все разделы и настройки",
                                "📖 Menu — all sections and settings"),
    "start_config":            ("⚙️ <code>кульш конфиг</code> — тонкая настройка под тебя",
                                "⚙️ <code>kulsh config</code> — tune the bot"),

    "btn_open_mini":           ("🚀 Открыть Mini App", "🚀 Open Mini App"),
    "btn_settings":            ("⚙️ Настройки", "⚙️ Settings"),
    "btn_commands":            ("📖 Команды", "📖 Commands"),
    "btn_menu":                ("📖 Меню", "📖 Menu"),
    "btn_donate":              ("💎 Донат", "💎 Donate"),
    "btn_github":              ("🔗 GitHub", "🔗 GitHub"),
    "btn_close":               ("❌ Закрыть", "❌ Close"),

    # ---- ДОНАТ ----
    "donate_title":            ("💎 Поддержать Кульша", "💎 Support Kulsh"),
    "donate_intro": (
        "💖 Донаты идут на серверы, домены и дальнейшую разработку проекта.",
        "💖 Donations go to servers, domains and further development.",
    ),
    "donate_methods":          ("💰 Способы:", "💰 Methods:"),
    "donate_online":           ("💳 Онлайн-донат", "💳 Online donation"),
    "donate_stars_hint":       ("⭐ Telegram Stars — <code>/donate_stars &lt;N&gt;</code>",
                                "⭐ Telegram Stars — <code>/donate_stars &lt;N&gt;</code>"),
    "donate_stars_need":       ("Укажите количество звёзд: <code>/donate_stars 100</code>",
                                "Specify star amount: <code>/donate_stars 100</code>"),
    "donate_stars_bad":        ("Неверное количество звёзд.", "Invalid star amount."),
    "donate_thanks":           ("🍷🗿 Спасибо за {0} звёзд, кент!", "🍷🗿 Thanks for {0} stars, mate!"),
    "donate_invoice_fail":     ("Не удалось выставить счёт: {0}", "Failed to create invoice: {0}"),
    "credits_balance":         ("💎 Кредиты: {0}/{1}", "💎 Credits: {0}/{1}"),

    "top_donators_title":      ("🏆 Топ донатеров:", "🏆 Top donators:"),
    "top_donators_empty":      ("Пока никто не донатил. Будь первым, бро 🍷🗿\n{0}",
                                "No donations yet. Be the first, bro 🍷🗿\n{0}"),
    "top_donators_item":       ("{0}. {1} — {2} очков", "{0}. {1} — {2} points"),

    "avatar_fail":             ("не смог получить аватарку", "failed to fetch avatar"),
    "avatar_none":             ("у {0} аватарки нет, пусто", "{0} has no avatar"),
    "recall_fail":             ("не нашёл ничего в памяти", "nothing found in memory"),

    "psl_need_photo":          ("📸 Жду фото для анализа. Отправь его с пометкой 'looksmaxxing'.",
                                "📸 Waiting for a photo. Send it marked 'looksmaxxing'."),
    "psl_analyzing":           ("⏳ Анализирую внешность...", "⏳ Analyzing your face..."),
    "psl_report":              ("📊 Результаты looksmaxxing", "📊 Looksmaxxing results"),
    "psl_title":               ("📊 РЕЗУЛЬТАТЫ LOOKSMAXXING", "📊 LOOKSMAXXING RESULTS"),
    "psl_gender":              ("🧬 Пол:", "🧬 Gender:"),
    "psl_score":               ("📈 PSL:", "📈 PSL:"),
    "psl_tier":                ("👑 Tier:", "👑 Tier:"),
    "psl_potential":           ("🔮 Потенциал:", "🔮 Potential:"),
    "psl_analysis":            ("📝 Анализ:", "📝 Analysis:"),
    "psl_advice":              ("⚡ Рекомендации:", "⚡ Recommendations:"),

    "battle_need_photos":      ("Для баттла пришлите два фото одним альбомом с командой 'кульш баттл'.",
                                "For a battle, send two photos in a single album with 'kulsh battle'."),
    "battle_waiting":          ("⚔️ Сравниваю лица...", "⚔️ Comparing faces..."),
    "battle_caption":          ("⚔️ Результат баттла", "⚔️ Battle result"),
    "battle_title":            ("⚔️ РЕЗУЛЬТАТ БАТТЛА", "⚔️ BATTLE RESULT"),
    "battle_winner":           ("🥇 Победитель:", "🥇 Winner:"),
    "battle_first":            ("Первое фото", "First photo"),
    "battle_second":           ("Второе фото", "Second photo"),
    "battle_reason":           ("🔍 Причина:", "🔍 Reason:"),
    "battle_photo1":           ("📊 Фото 1:", "📊 Photo 1:"),
    "battle_photo2":           ("📊 Фото 2:", "📊 Photo 2:"),

    "logs_no_access":          ("не для тебя писано", "not for you"),
    "logs_cant_check":         ("не могу проверить права", "cannot verify permissions"),
    "logs_read_error":         ("Ошибка чтения логов: {0}", "Log read error: {0}"),

    "tool_unpacking":          ("📦 Распаковываю архив...", "📦 Unpacking archive..."),
    "tool_unpacked":           ("📦 Распаковал.\n\n📄 {0}", "📦 Unpacked.\n\n📄 {0}"),
    "tool_analyzing":          ("🧠 Анализирую {0} файл(ов)...", "🧠 Analyzing {0} file(s)..."),
    "tool_editing":            ("✏️ Редактирую {0} файл(ов)...", "✏️ Editing {0} file(s)..."),
    "tool_repacking":          ("🗜 Собираю архив обратно...", "🗜 Repacking archive..."),
    "tool_sending":            ("📤 Отправляю готовый архив...", "📤 Sending the archive..."),
    "tool_done":               ("✅ Готово", "✅ Done"),
    "tool_error":              ("❌ Ошибка: {0}", "❌ Error: {0}"),
    "tool_no_changes":         ("🤔 ИИ не предложил изменений. {0}", "🤔 AI made no changes. {0}"),
    "tool_parse_fail":         ("❌ Не смог распарсить ответ ИИ: {0}", "❌ Failed to parse AI response: {0}"),
    "tool_no_credits": (
        "💎 Недостаточно кредитов для редактирования архива.\nНужно {0}, у тебя {1}/{2}.",
        "💎 Not enough credits to edit the archive.\nNeed {0}, you have {1}/{2}.",
    ),
    "tool_download_fail":      ("не смог скачать файл: {0}", "failed to download file: {0}"),
    "tool_review_empty":       ("что тут?", "what's here?"),

    "ai_error_400":            ("Ошибка запроса к API (400).", "API request error (400)."),
    "ai_error_generic":        ("Ошибка API.", "API error."),
    "ai_blocked":              ("Блокировка контента.", "Content blocked."),
    "ai_unknown":              ("Ошибка. Что-то пошло не так.", "Error. Something went wrong."),
    "ai_no_models":            ("Все модели и ключи недоступны, попробуй позже 🍷🗿",
                                "All models and keys are unavailable, try later 🍷🗿"),
    "ai_json_fail":            ("Не удалось распарсить ответ ИИ.", "Failed to parse AI response."),
    "ai_custom_prefix":        ("Твои обязательные инструкции: ", "Your mandatory instructions: "),

    "on":                      ("вкл", "on"),
    "off":                     ("выкл", "off"),
    "dark":                    ("тёмная", "dark"),
    "light":                   ("светлая", "light"),
    "russian":                 ("Русский 🇷🇺", "Russian 🇷🇺"),
    "english":                 ("Английский 🇬🇧", "English 🇬🇧"),

    # ---- поиск ----
    "search_starting":         ("🔎 Ищу: {0}", "🔎 Searching: {0}"),
    "search_nothing":          ("🔎 Ничего не нашёл по запросу.", "🔎 Nothing found."),
    "search_off":              ("🔎 Веб-поиск выключен в настройках.",
                                "🔎 Web search is disabled in settings."),
    "search_need_query":       ("Использование: <code>кульш поиск &lt;запрос&gt;</code>",
                                "Usage: <code>kulsh search &lt;query&gt;</code>"),
    "search_source":           ("Источник", "Source"),
    "search_results_header":   ("🔎 Результаты поиска по запросу: {0}",
                                "🔎 Search results for: {0}"),

    # ---- chart ----
    "chart_error":             ("❌ Не удалось построить график: {0}", "❌ Chart error: {0}"),
    "chart_built":             ("📊 Инфографика готова", "📊 Infographic ready"),
    "chart_building":          ("📊 Строю инфографику...", "📊 Rendering infographic..."),
    "chart_usage":             ("Использование: <code>кульш график &lt;описание&gt;</code>",
                                "Usage: <code>kulsh chart &lt;description&gt;</code>"),

    # ---- Discord ----
    "ds_only_admins":          ("только админы могут менять конфиг", "only admins can change config"),
    "ds_need_specify_ru_en":   ("Укажите <code>ru</code> или <code>en</code>.", "Specify <code>ru</code> or <code>en</code>."),
    "ds_need_specify_theme":   ("Укажите <code>тёмная</code> или <code>светлая</code>.", "Specify <code>dark</code> or <code>light</code>."),
    "ds_setting_lang":         ("Язык: {0}", "Language: {0}"),
    "ds_setting_theme":        ("Тема: {0}", "Theme: {0}"),
    "ds_setting_series":       ("Серия: {0}", "Series: {0}"),
    "ds_setting_stickers":     ("Стикеры: {0}", "Stickers: {0}"),
    "ds_setting_sep":          ("Разбивка: {0}", "Split: {0}"),
    "ds_setting_autoreply":    ("Автоответ: {0}", "Auto-reply: {0}"),
    "ds_setting_random":       ("Рандом: {0}", "Random: {0}"),
    "ds_setting_websearch":    ("Веб-поиск: {0}", "Web search: {0}"),
    "ds_setting_temp":         ("Температура: {0}", "Temperature: {0}"),
    "ds_setting_prompt_reset": ("Промпт сброшен", "Prompt reset"),
    "ds_setting_prompt_set":   ("Промпт установлен", "Prompt set"),
    "ds_setting_prompt_need":  ("Введите текст или 'сброс'", "Send text or 'reset'"),
    "ds_setting_model":        ("Модель: {0}", "Model: {0}"),
    "ds_setting_model_auto":   ("Модель: авто", "Model: auto"),
    "ds_setting_model_bad":    ("Введите номер или 'авто'.", "Enter number or 'auto'."),
    "ds_setting_model_badnum": ("Неверный номер", "Invalid number"),
    "ds_setting_temp_bad":     ("Введите число 0.0-2.0", "Enter number 0.0-2.0"),
    "ds_unknown_param":        ("Неизвестный параметр. Используйте 'кульш конфиг'.",
                                "Unknown parameter. Use 'kulsh config'."),
    "ds_update_no_access":     ("ты кто бля, обновлять меня будешь?", "who are you to update me?"),
    "ds_update_start":         ("ща попробую обновиться (с автооткатом при ошибке)...",
                                "trying to update (auto-rollback on error)..."),
    "ds_update_uptodate":      ("я и так свежий:\n```\n{0}\n```", "already up to date:\n```\n{0}\n```"),
    "ds_update_ok":            ("изменения подтянуты, перезапускаюсь:\n```\n{0}\n```",
                                "changes pulled, restarting:\n```\n{0}\n```"),
    "ds_update_rolled": (
        "новый коммит содержит ошибки — я откатился к предыдущей версии. "
        "Бот продолжает работать.\n```\n{0}\n```",
        "new commit contains errors — rolled back. Bot continues working.\n```\n{0}\n```",
    ),
    "ds_update_error":         ("ошибка обновления:\n```\n{0}\n```", "update error:\n```\n{0}\n```"),
    "ds_voice_not_in":         ("ты не в войсе, куда заходить?", "you're not in voice, where should I go?"),
    "ds_voice_joined":         ("залетел в {0} 🍷🗿", "joined {0} 🍷🗿"),
    "ds_voice_cant_join":      ("не могу зайти.", "cannot join."),
    "ds_voice_left":           ("пока кенты", "bye mates"),
    "ds_voice_not_in_bot":     ("я и так не там", "I'm not there anyway"),
    "ds_attachments_error":    ("не могу глянуть, сломалась", "cannot look, broken"),
    "ds_no_memory":            ("не нашёл ничего в памяти", "nothing found in memory"),
    "ds_avatar_none":          ("не смог получить аватарку", "failed to fetch avatar"),
    "ds_logs_content":         ("🍷🗿 Логи сервера:", "🍷🗿 Server logs:"),

    "help_body": (
        "🍷🗿 <b>Команды Кульша</b>\n\n"
        "<b>Общие:</b>\n"
        "/start — приветствие\n"
        "/menu — интерактивное меню\n"
        "/help — эта справка\n"
        "/donate — поддержать проект\n"
        "/donate_stars &lt;N&gt; — донат через Telegram Stars\n"
        "/credits — баланс кредитов\n\n"
        "<b>Настройки:</b>\n"
        "<code>кульш конфиг</code> — настройки (инлайн)\n\n"
        "<b>Утилиты:</b>\n"
        "<code>кульш аватарка</code> — описать аватарку\n"
        "<code>кульш вспомни медиа [N]</code> — вспомнить N медиа\n"
        "<code>кульш поиск &lt;запрос&gt;</code> — поиск в интернете\n"
        "<code>кульш график &lt;описание&gt;</code> — сгенерировать инфографику\n"
        "<code>кульш логи</code> — логи (админам)\n\n"
        "<b>Развлечения:</b>\n"
        "<code>кульш psl</code> — looksmaxxing\n"
        "<code>кульш psl совет</code> — + рекомендации\n"
        "<code>кульш battle</code> — баттл (альбом)\n"
        "<code>кульш донаты</code> — топ донатеров\n\n"
        "<b>Инструменты (ЛС):</b>\n"
        "Отправь архив/текстовый файл — бот распакует, изменит, соберёт и вернёт.\n\n"
        "🚀 Mini App: {0}\n"
        "🔗 GitHub: {1}",
        "🍷🗿 <b>Kulsh commands</b>\n\n"
        "<b>General:</b>\n"
        "/start — greeting\n"
        "/menu — interactive menu\n"
        "/help — this help\n"
        "/donate — support the project\n"
        "/donate_stars &lt;N&gt; — donate via Telegram Stars\n"
        "/credits — credits balance\n\n"
        "<b>Settings:</b>\n"
        "<code>kulsh config</code> — settings (inline)\n\n"
        "<b>Utilities:</b>\n"
        "<code>kulsh avatar</code> — describe avatar\n"
        "<code>kulsh recall [N]</code> — recall N media\n"
        "<code>kulsh search &lt;query&gt;</code> — web search\n"
        "<code>kulsh chart &lt;description&gt;</code> — generate infographic\n"
        "<code>kulsh logs</code> — logs (admins)\n\n"
        "<b>Entertainment:</b>\n"
        "<code>kulsh psl</code> — looksmaxxing\n"
        "<code>kulsh psl advice</code> — + recommendations\n"
        "<code>kulsh battle</code> — battle (album)\n"
        "<code>kulsh donations</code> — top donators\n\n"
        "<b>Tools (DM):</b>\n"
        "Send an archive/text file — bot unpacks, edits, repacks and returns it.\n\n"
        "🚀 Mini App: {0}\n"
        "🔗 GitHub: {1}",
    ),
}


def _t(lang: str, key: str, *args: Any, **kwargs: Any) -> str:
    entry = TEXTS.get(key)
    if not entry:
        return key
    ru, en = entry
    text = ru if lang == "ru" else en
    if args or kwargs:
        try:
            return text.format(*args, **kwargs)
        except Exception:
            return text
    return text


def _html_to_md(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<u>(.*?)</u>', r'__\1__', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<ins>(.*?)</ins>', r'__\1__', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<s>(.*?)</s>', r'~~\1~~', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<strike>(.*?)</strike>', r'~~\1~~', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<del>(.*?)</del>', r'~~\1~~', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<pre>(.*?)</pre>', lambda m: '```\n' + m.group(1) + '\n```', text, flags=re.DOTALL | re.IGNORECASE)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text

# ============================================================
# VOICE / TTS
# ============================================================
voice_recv: Any = None
sr: Any = None
AudioSegment: Any = None
edge_tts: Any = None
try:
    from discord.ext import voice_recv as _voice_recv
    voice_recv = _voice_recv
    VOICE_RECV_AVAILABLE = True
except ImportError:
    VOICE_RECV_AVAILABLE = False

DISCORD_VERSION = tuple(map(int, discord.__version__.split('.')))
VOICE_RECOGNITION_ENABLED = DISCORD_VERSION >= (2, 0, 0) and VOICE_RECV_AVAILABLE
if VOICE_RECOGNITION_ENABLED:
    try:
        import speech_recognition as _sr
        from pydub import AudioSegment as _AudioSegment
        sr = _sr
        AudioSegment = _AudioSegment
    except ImportError:
        VOICE_RECOGNITION_ENABLED = False
        logger.info("⚠️ speech_recognition/pydub не найдены")
else:
    logger.info(f"⚠️ discord.py {discord.__version__}, voice_recv недоступен")

try:
    import edge_tts as _edge_tts
    from discord import FFmpegPCMAudio
    edge_tts = _edge_tts
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False
    logger.info("⚠️ edge_tts/FFmpeg не найдены")

# ============================================================
# TYPING HELPERS
# ============================================================
JsonDict: TypeAlias = dict[str, Any]
Color: TypeAlias = str | tuple[int, int, int]
Font: TypeAlias = ImageFont.FreeTypeFont | ImageFont.ImageFont
SearchHit: TypeAlias = dict[str, str]
ChartTheme: TypeAlias = dict[str, Any]
SeriesSpec: TypeAlias = dict[str, Any]
_HandlerT = TypeVar("_HandlerT", bound=Callable[..., Any])


class _TypedHandler(Protocol):
    def __call__(self, handler: _HandlerT) -> _HandlerT: ...


def _typed_decorator(decorator: Callable[..., Any]) -> Callable[..., _TypedHandler]:
    """pyTelegramBotAPI decorators are untyped; preserve the wrapped callable."""
    return cast(Callable[..., _TypedHandler], decorator)


def _cb_id(call: telebot.types.CallbackQuery) -> int:
    """Library stubs type callback query ids as int; the API sends strings."""
    return cast(int, call.id)


def _tg_msg(call: telebot.types.CallbackQuery) -> telebot.types.Message:
    message = call.message
    if not isinstance(message, telebot.types.Message):
        raise RuntimeError("callback has no accessible message")
    return message


def _ds_user(bot: discord.Client) -> discord.ClientUser:
    user = bot.user
    if user is None:
        raise RuntimeError("discord bot is not ready")
    return user


def _as_member(user: discord.abc.User) -> discord.Member | None:
    return user if isinstance(user, discord.Member) else None


def _voice_client(guild: discord.Guild | None) -> discord.VoiceClient | None:
    if guild is None or guild.voice_client is None:
        return None
    client = guild.voice_client
    return client if isinstance(client, discord.VoiceClient) else None


def _messageable(channel: discord.abc.Messageable | None) -> discord.abc.Messageable | None:
    if channel is None:
        return None
    send = getattr(channel, "send", None)
    return channel if callable(send) else None


def _json_dict(value: Any) -> JsonDict:
    if isinstance(value, dict):
        return cast(JsonDict, value)
    return {}


def _json_str(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _theme_str(theme: ChartTheme, key: str, default: str = "#000000") -> str:
    value = theme.get(key, default)
    return value if isinstance(value, str) else default

# ============================================================
# ГЛОБАЛЬНЫЕ СТРУКТУРЫ
# ============================================================
chat_memories: dict[str, deque[dict[str, Any]]] = {}
voice_text_channels: dict[int, Any] = {}
donations_data: dict[str, Any] = {}
user_configs: defaultdict[str, dict[str, Any]] = defaultdict(dict)
config_msg_owners: dict[int, int] = {}
config_trigger_msgs: dict[str, int] = {}
prompt_waiting: dict[int, int] = {}
config_children_msgs: dict[tuple[int, int], list[int]] = {}
credits_data: dict[str, dict[str, Any]] = {}
tools_sessions: dict[int, dict[str, Any]] = {}
chat_media_history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=50))
last_random_reply: dict[str, float] = {}
last_old_reply: dict[str, float] = {}
battle_media_groups: dict[str, asyncio.Task[None]] = {}
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
def load_json_file(path: str) -> JsonDict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return _json_dict(json.load(f))
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


def save_long_term_memory(data: JsonDict) -> None:
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
    "web_search_enabled": True,
}


def get_user_config(platform: str, chat_id: int, user_id: int) -> JsonDict:
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


def add_user_memory(
    chat_id: str,
    platform: str,
    display_name: str | None,
    username: str | None,
    user_id: int,
    text: str | None,
    media: list[str] | None = None,
    message_id: int | None = None,
) -> None:
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


def add_media_history(
    chat_id: str,
    url: str | None,
    media_type: str,
    sender: str,
    file_id: str | None = None,
    caption: str = "",
) -> None:
    chat_media_history[chat_id].append({
        "url": url, "type": media_type, "sender": sender,
        "file_id": file_id, "caption": caption,
        "time": msk_now().strftime('%d.%m %H:%M'),
    })

# ============================================================
# HTML / MARKDOWN (fallback)
# ============================================================
def markdown_like_to_telegram_html(text: str) -> str:
    if not text:
        return ""
    text = html.escape(text, quote=False)
    text = re.sub(r'```([\s\S]*?)```', lambda m: '<pre>' + m.group(1) + '</pre>', text)
    text = re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)', r'<i>\1</i>', text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text, flags=re.DOTALL)
    for tag in ("code", "b", "i", "u", "s", "pre"):
        text = text.replace(f'&lt;{tag}&gt;', f'<{tag}>').replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    text = text.replace('&lt;a href=', '<a href=').replace('&lt;/a&gt;', '</a>')
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


async def typing_with_delay_ds(
    channel: discord.abc.Messageable, text: str, delay: float | None = None,
) -> None:
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
# RICH MESSAGE
# ============================================================
def _parse_inline(text: str) -> Any:
    if not text:
        return ""
    text = _html_to_md(text)
    parts: list[Any] = []
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf:
            parts.append(buf)
            buf = ""

    i = 0
    n = len(text)
    while i < n:
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end != -1:
                flush()
                parts.append({"type": "bold", "text": _parse_inline(text[i + 2:end])})
                i = end + 2
                continue
        if text.startswith("__", i):
            end = text.find("__", i + 2)
            if end != -1:
                flush()
                parts.append({"type": "underline", "text": _parse_inline(text[i + 2:end])})
                i = end + 2
                continue
        if text.startswith("~~", i):
            end = text.find("~~", i + 2)
            if end != -1:
                flush()
                parts.append({"type": "strikethrough", "text": _parse_inline(text[i + 2:end])})
                i = end + 2
                continue
        if text.startswith("$$", i):
            end = text.find("$$", i + 2)
            if end != -1:
                flush()
                parts.append({"type": "mathematical_expression", "expression": text[i + 2:end]})
                i = end + 2
                continue
        if text[i] == "*" and not text.startswith("**", i):
            end = text.find("*", i + 1)
            if end != -1 and not text.startswith("**", end):
                flush()
                parts.append({"type": "italic", "text": _parse_inline(text[i + 1:end])})
                i = end + 1
                continue
        if text[i] == "_" and not text.startswith("__", i):
            end = text.find("_", i + 1)
            if end != -1 and not text.startswith("__", end):
                flush()
                parts.append({"type": "italic", "text": _parse_inline(text[i + 1:end])})
                i = end + 1
                continue
        if text[i] == "`":
            end = text.find("`", i + 1)
            if end != -1:
                flush()
                parts.append({"type": "code", "text": text[i + 1:end]})
                i = end + 1
                continue
        if text[i] == "[":
            m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', text[i:])
            if m:
                flush()
                parts.append({"type": "url", "text": m.group(1), "url": m.group(2)})
                i += m.end()
                continue
        buf += text[i]
        i += 1

    flush()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return parts


def _make_cell(raw: str) -> JsonDict:
    """Ячейка таблицы. *...* → is_header=True (залитая). Все ячейки по центру."""
    s = (raw or "").strip()
    is_header = False
    inner = s
    if len(s) >= 2 and s.startswith('*') and s.endswith('*') and '*' not in s[1:-1]:
        inner = s[1:-1]
        is_header = True
    cell: dict[str, Any] = {"text": _parse_inline(inner), "align": "center"}
    if is_header:
        cell["is_header"] = True
    return cell


def _text_to_blocks(text: str) -> list[JsonDict]:
    if not text:
        return []
    text = _html_to_md(text)
    lines = text.split('\n')
    blocks: list[JsonDict] = []
    i = 0
    n = len(lines)
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    table_rows: list[list[JsonDict]] = []

    def flush_code() -> None:
        nonlocal in_code, code_lang, code_lines
        if code_lines:
            block: dict[str, Any] = {"type": "pre", "text": '\n'.join(code_lines)}
            if code_lang:
                block["language"] = code_lang
            blocks.append(block)
        in_code = False
        code_lang = ""
        code_lines = []

    def flush_table() -> None:
        nonlocal table_rows
        if table_rows:
            blocks.append({
                "type": "table",
                "cells": table_rows,
                "is_bordered": True,
            })
        table_rows = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith('```'):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
                code_lines = []
            else:
                flush_code()
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if stripped.startswith('|') and stripped.endswith('|') and len(stripped) >= 2:
            inner = stripped.strip('|')
            cells_raw = inner.split('|')
            if cells_raw and all(re.match(r'^\s*:?-+:?\s*$', c) for c in cells_raw):
                i += 1
                continue
            table_rows.append([_make_cell(c) for c in cells_raw])
            i += 1
            continue
        else:
            flush_table()

        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            blocks.append({
                "type": "heading",
                "text": _parse_inline(m.group(2)),
                "size": level,
            })
            i += 1
            continue

        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            blocks.append({"type": "divider"})
            i += 1
            continue

        if re.match(r'^-\s*\[[ x]\]', line):
            items: list[JsonDict] = []
            while i < n and re.match(r'^-\s*\[[ x]\]', lines[i]):
                checked = '[x]' in lines[i].lower()
                item_text = re.sub(r'^-\s*\[[ x]\]\s*', '', lines[i])
                item: dict[str, Any] = {
                    "blocks": [{"type": "paragraph", "text": _parse_inline(item_text)}],
                    "has_checkbox": True,
                }
                if checked:
                    item["is_checked"] = True
                items.append(item)
                i += 1
            blocks.append({"type": "list", "items": items})
            continue

        if re.match(r'^[-*+]\s', line):
            bullet_items: list[JsonDict] = []
            while i < n and re.match(r'^[-*+]\s', lines[i]):
                item_text = re.sub(r'^[-*+]\s', '', lines[i])
                bullet_items.append({
                    "blocks": [{"type": "paragraph", "text": _parse_inline(item_text)}],
                })
                i += 1
            blocks.append({"type": "list", "items": bullet_items})
            continue

        if re.match(r'^\d+\.\s', line):
            numbered_items: list[JsonDict] = []
            while i < n and re.match(r'^\d+\.\s', lines[i]):
                item_text = re.sub(r'^\d+\.\s', '', lines[i])
                numbered_items.append({
                    "blocks": [{"type": "paragraph", "text": _parse_inline(item_text)}],
                })
                i += 1
            blocks.append({"type": "list", "items": numbered_items})
            continue

        if stripped.startswith('>'):
            quote_lines: list[str] = []
            while i < n and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({
                "type": "blockquote",
                "blocks": [{"type": "paragraph", "text": _parse_inline(' '.join(quote_lines))}],
            })
            continue

        if not stripped:
            i += 1
            continue

        blocks.append({
            "type": "paragraph",
            "text": _parse_inline(line),
        })
        i += 1

    flush_code()
    flush_table()
    return blocks


def _looks_like_rich(text: str) -> bool:
    if not text:
        return False
    return bool(
        re.search(r'^#{1,6}\s', text, re.MULTILINE) or
        re.search(r'^\|.*\|', text, re.MULTILINE) or
        re.search(r'^[-*+]\s', text, re.MULTILINE) or
        re.search(r'^\d+\.\s', text, re.MULTILINE) or
        re.search(r'^-\s*\[[ x]\]', text, re.MULTILINE) or
        re.search(r'^>\s', text, re.MULTILINE) or
        '```' in text or
        re.search(r'\$\$.+?\$\$', text, re.DOTALL) or
        re.search(r'<(b|strong|i|em|u|ins|s|strike|del|code|pre|a)\b', text, re.IGNORECASE)
    )


def build_rich_message(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    if not _looks_like_rich(text):
        return None
    try:
        blocks = _text_to_blocks(text)
    except Exception as e:
        logger.warning(f"build_rich_message parse error: {e}")
        return None
    if not blocks:
        return None
    return {
        "blocks": blocks,
        "is_rtl": False,
        "skip_entity_detection": False,
    }


def _is_button_type_error(err_text: str) -> bool:
    return "BUTTON_TYPE_INVALID" in err_text


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

    async def _try_post(markup: InlineKeyboardMarkup | None) -> tuple[int, str]:
        payload: dict[str, Any] = {"chat_id": chat_id, "rich_message": rich}
        if reply_to:
            payload["reply_parameters"] = {"message_id": reply_to}
        if markup is not None:
            try:
                payload["reply_markup"] = _json_dict(cast(Any, markup).to_dict())
            except AttributeError:
                payload["reply_markup"] = markup
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendRichMessage"
            async with session.post(url, json=payload, timeout=30) as resp:
                body = await resp.text()
                return resp.status, body

    try:
        status, body = await _try_post(reply_markup)
        if status == 200:
            return True
        if status == 400 and _is_button_type_error(body) and reply_markup is not None:
            logger.warning("sendRichMessage BUTTON_TYPE_INVALID — повтор без клавиатуры")
            status, body = await _try_post(None)
            if status == 200:
                return True
        logger.warning(f"sendRichMessage {status}: {body[:400]}")
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

    async def _try_edit(markup: InlineKeyboardMarkup | None) -> tuple[int, str]:
        payload: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id, "rich_message": rich}
        if markup is not None:
            try:
                payload["reply_markup"] = _json_dict(cast(Any, markup).to_dict())
            except AttributeError:
                payload["reply_markup"] = markup
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/editMessageText"
            async with session.post(url, json=payload, timeout=30) as resp:
                body = await resp.text()
                return resp.status, body

    try:
        status, body = await _try_edit(reply_markup)
        if status == 200:
            return True
        if status == 400 and _is_button_type_error(body) and reply_markup is not None:
            logger.warning("editMessageText(rich) BUTTON_TYPE_INVALID — повтор без клавиатуры")
            status, body = await _try_edit(None)
            if status == 200:
                return True
        logger.warning(f"editMessageText(rich) {status}: {body[:400]}")
        return False
    except Exception as e:
        logger.warning(f"edit_rich_message error: {e}")
        return False


async def send_formatted(
    chat_id: int,
    text: str,
    reply_to: int | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    sent_ok = await send_rich_message(chat_id, text, reply_to=reply_to, reply_markup=reply_markup)
    if sent_ok:
        return
    html_text = markdown_like_to_telegram_html(text)
    try:
        await tg_bot.send_message(
            chat_id, html_text, parse_mode='HTML',
            reply_to_message_id=reply_to, reply_markup=reply_markup,
        )
    except Exception as e:
        err = str(e)
        if _is_button_type_error(err) and reply_markup is not None:
            logger.warning("HTML send BUTTON_TYPE_INVALID — повтор без клавиатуры")
            try:
                await tg_bot.send_message(
                    chat_id, html_text, parse_mode='HTML',
                    reply_to_message_id=reply_to, reply_markup=None,
                )
                return
            except Exception as e2:
                err = str(e2)
        logger.warning(f"html send failed: {err}; trying plain")
        plain = re.sub(r'<[^>]+>', '', html_text)
        try:
            await tg_bot.send_message(
                chat_id, plain, reply_to_message_id=reply_to, reply_markup=reply_markup,
            )
        except Exception as e2:
            if _is_button_type_error(str(e2)) and reply_markup is not None:
                try:
                    await tg_bot.send_message(
                        chat_id, plain, reply_to_message_id=reply_to, reply_markup=None,
                    )
                    return
                except Exception as e3:
                    logger.error(f"plain fallback fail: {e3}")
                    return
            logger.error(f"plain fallback fail: {e2}")


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
# АНИМАЦИЯ ПРИМЕНЕНИЯ НАСТРОЕК (медленнее)
# ============================================================
APPLY_ANIMATION_FRAMES = [
    "🍷🗿",
    "🗿🍷",
    "🍷🗿",
]


async def _edit_plain_safe(chat_id: int, message_id: int, text: str, attempts: int = 3) -> bool:
    for _ in range(attempts):
        try:
            await tg_bot.edit_message_text(text, chat_id, message_id)
            return True
        except Exception as e:
            err = str(e)
            if "message is not modified" in err:
                return True
            if "Too Many Requests" in err or "retry after" in err.lower():
                m = re.search(r'retry after (\d+)', err, re.IGNORECASE)
                wait = float(m.group(1)) if m else 1.0
                await asyncio.sleep(wait)
                continue
            return False
    return False


async def play_apply_animation(chat_id: int, message_id: int, step_delay: float = 0.85) -> None:
    try:
        for frame in APPLY_ANIMATION_FRAMES:
            await _edit_plain_safe(chat_id, message_id, frame)
            await asyncio.sleep(step_delay)
        try:
            await tg_bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"play_apply_animation: {e}")


async def _cleanup_config_children(chat_id: int, user_id: int) -> None:
    keys = list(config_children_msgs.keys())
    for key in keys:
        if key[0] != chat_id or key[1] != user_id:
            continue
        for mid in config_children_msgs.pop(key, []):
            try:
                await tg_bot.delete_message(chat_id, mid)
            except Exception:
                pass

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
    else:
        parts.append("ФОРМАТИРОВАНИЕ: расширенный режим отключён. Пиши простым текстом.\n\n")

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

    if cfg.get("web_search_enabled", True):
        parts.append(
            "\n\n🔎 ВЕБ-ПОИСК. Ты можешь искать актуальную информацию в интернете. Если пользователь спрашивает "
            "о свежих событиях, фактах, ценах, новостях или чём-то, чего ты точно не знаешь — твой ответ должен "
            "НАЧИНАТЬСЯ со строки `!search <поисковый запрос>` и не содержать ничего больше. Бот выполнит поиск, "
            "и ты получишь результаты, после чего дашь финальный ответ. Пример:\n"
            "!search погода в москве завтра\n\n"
            "Не используй !search для общих знаний или болтовни."
        )

    if premium_functions_enabled:
        parts.append(
            "\n\n📊 ГЕНЕРАЦИЯ ИНФОГРАФИКИ. Ты можешь сгенерировать красивое инфографическое изображение. "
            "Для этого включи в ответ блок:\n"
            "!chart\n```json\n{...JSON-спецификация...}\n```\n"
            "Спецификация (JSON):\n"
            "{\n"
            '  "theme": "dark_modern" | "light_minimal" | "ocean" | "retro",\n'
            '  "title": "Заголовок",\n'
            '  "subtitle": "Подзаголовок (опц.)",\n'
            '  "blocks": [\n'
            '    {"type": "heading", "text": "..."},\n'
            '    {"type": "text", "text": "..."},\n'
            '    {"type": "divider"},\n'
            '    {"type": "bar", "title": "...", "labels": ["A","B"], "values": [10,20], "height": 320},\n'
            '    {"type": "line", "title": "...", "x": ["Jan","Feb"], "series": [{"name":"S1","y":[1,2]}], "height": 320},\n'
            '    {"type": "pie", "title": "...", "labels": ["A","B"], "values": [10,20], "height": 340},\n'
            '    {"type": "pie3d", "title": "...", "labels": ["A","B"], "values": [10,20], "height": 340},\n'
            '    {"type": "table", "title": "...", "headers": ["A","B"], "rows": [["1","2"],["3","4"]]},\n'
            '    {"type": "image", "url": "https://..."},\n'
            '    {"type": "image", "source": "user", "index": 0}\n'
            "  ]\n"
            "}\n"
            "Используй !chart когда уместно: для сравнений, статистики, диаграмм, отчётов. "
            "Числа в values должны быть реальными числами (не строками). "
            "Цвета опционально можно указать массивом hex-строк в поле \"colors\". "
            "Размер по умолчанию 1400x1000, высота расширяется автоматически под блоки."
        )

    mem_key = str(chat_id)
    if mem_key in long_term_memory:
        mem_data = _json_dict(long_term_memory[mem_key])
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
) -> str:
    lang = "ru"
    if chat_id is not None and user_id is not None:
        lang = get_user_config(platform, chat_id, user_id).get("language", "ru")

    if system_instruction_override is not None:
        base_context = system_instruction_override
    else:
        if chat_id is not None and user_id is not None:
            base_context = build_system_prompt(platform, chat_id, user_id)
        else:
            base_context = build_system_prompt(platform, chat_id or 0, user_id or 0)

    if context_type == "random":
        prompt = ("Напиши рандомную мысль или шутку в чат. Без разметки markdown. Можно разбить на 1-2 сообщения "
                  "через !separate, если хочется."
                  if lang == "ru" else
                  "Write a random thought or joke. No markdown. Can split into 1-2 messages via !separate.")
    elif context_type == "caption":
        prompt = ("Пользователь попросил фото. Придумай короткую подпись в своём стиле."
                  if lang == "ru" else
                  "User requested a photo. Come up with a short caption.")
    elif context_type == "observer":
        prompt = (
            "Ты молча наблюдаешь за чатом. Если хочешь что-то коротко прокомментировать — напиши одно короткое "
            "сообщение в стиле Кульша. Если не хочешь — ответь ровно 'НЕТ'."
            if lang == "ru" else
            "You silently observe the chat. If you want to comment, write one short message in Kulsh's style. "
            "If not — reply exactly 'NO'."
        )

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
            logger.info(f"🔄 {total_attempt}/{total_max}: {model_name}, ключ {api_key[:4]}...")
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
                            return _t(lang, "ai_error_400")
                        if status >= 500:
                            await asyncio.sleep(backoff)
                            continue
                        if status != 200:
                            text = await resp.text()
                            logger.error(f"{status}: {text[:300]}")
                            return _t(lang, "ai_error_generic")
                        data = _json_dict(await resp.json())
                        if 'candidates' in data and data['candidates']:
                            try:
                                candidate = data['candidates'][0]
                                content = _json_dict(candidate.get('content') if isinstance(candidate, dict) else None)
                                parts_raw = content.get('parts')
                                first = parts_raw[0] if isinstance(parts_raw, list) and parts_raw else {}
                                return _json_str(_json_dict(first).get('text'))
                            except (KeyError, IndexError, TypeError):
                                continue
                        else:
                            if 'promptFeedback' in data:
                                br = _json_dict(data['promptFeedback']).get('blockReason', 'UNKNOWN')
                                logger.error(f"❌ Заблокировано: {br}")
                                return _t(lang, "ai_blocked")
                            await asyncio.sleep(backoff)
                            continue
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Сетевая ошибка: {e}")
                await asyncio.sleep(backoff)
                continue
            except Exception as e:
                logger.error(f"Непредвиденная ошибка: {e}")
                return _t(lang, "ai_unknown")
    return _t(lang, "ai_no_models")

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


async def extract_memory(chat_id: str, user_message: str, bot_answer: str) -> None:
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
# WEB SEARCH
# ============================================================
USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


async def web_search_ddg(query: str, max_results: int = 6) -> list[SearchHit]:
    """
    Поиск через DuckDuckGo HTML-версию. Без API-ключей, бесплатно.
    Пробуем сначала lite-интерфейс, потом обычный.
    """
    results: list[SearchHit] = []
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ru,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml",
    }
    endpoints = [
        ("https://lite.duckduckgo.com/lite/", {"q": query}),
        ("https://html.duckduckgo.com/html/", {"q": query}),
    ]
    async with aiohttp.ClientSession(headers=headers) as session:
        for url, data in endpoints:
            try:
                async with session.post(url, data=data, timeout=15,
                                        allow_redirects=True) as resp:
                    if resp.status != 200:
                        continue
                    page = await resp.text()
            except Exception as e:
                logger.debug(f"ddg search {url} err: {e}")
                continue

            # ---- lite version parsing ----
            # results are in <a rel="nofollow" href="..."> title </a> and next <td class="result-snippet">
            lite_pattern = re.compile(
                r'<a\s+rel="nofollow"\s+href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'<td\s+class="result-snippet">(.*?)</td>',
                re.DOTALL | re.IGNORECASE,
            )
            for m in lite_pattern.finditer(page):
                href = _ddg_unwrap(m.group(1))
                title = _strip_tags(m.group(2))
                snippet = _strip_tags(m.group(3))
                if href and title:
                    results.append({
                        "title": html.unescape(title).strip(),
                        "url": href,
                        "snippet": html.unescape(snippet).strip(),
                    })
                if len(results) >= max_results:
                    return results

            if len(results) >= max_results:
                return results

            # ---- html version parsing ----
            html_pattern = re.compile(
                r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                re.DOTALL | re.IGNORECASE,
            )
            for m in html_pattern.finditer(page):
                href = _ddg_unwrap(m.group(1))
                title = _strip_tags(m.group(2))
                snippet = _strip_tags(m.group(3))
                if href and title:
                    results.append({
                        "title": html.unescape(title).strip(),
                        "url": href,
                        "snippet": html.unescape(snippet).strip(),
                    })
                if len(results) >= max_results:
                    return results

            if results:
                return results

    return results[:max_results]


def _ddg_unwrap(url: str) -> str:
    if not url:
        return url
    if url.startswith("//"):
        url = "https:" + url
    if "duckduckgo.com/l/" in url:
        try:
            qs = parse_qs(urlparse(url).query)
            if "uddg" in qs:
                return unquote(qs["uddg"][0])
        except Exception:
            pass
    return url


def _strip_tags(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '')


async def web_search_wikipedia(query: str, max_results: int = 3) -> list[SearchHit]:
    """Wikipedia API — бесплатный, без ключей. Для фактов."""
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": max_results,
        }
        headers = {"User-Agent": USER_AGENT}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get("https://ru.wikipedia.org/w/api.php",
                                   params=params, timeout=10) as resp:
                if resp.status != 200:
                    return []
                data = _json_dict(await resp.json())
        out: list[SearchHit] = []
        query_obj = _json_dict(data.get("query"))
        search_items = query_obj.get("search", [])
        if not isinstance(search_items, list):
            search_items = []
        for item in search_items[:max_results]:
            item_d = _json_dict(item)
            title = _json_str(item_d.get("title"))
            snippet = _strip_tags(_json_str(item_d.get("snippet")))
            url = "https://ru.wikipedia.org/wiki/" + quote_plus(title.replace(" ", "_"))
            out.append({"title": title, "url": url, "snippet": snippet})
        return out
    except Exception as e:
        logger.debug(f"wiki search err: {e}")
        return []


async def web_search(query: str, max_results: int = 6) -> list[SearchHit]:
    """Комбинирует DDG + Wikipedia."""
    ddg_results = await web_search_ddg(query, max_results=max_results)
    if len(ddg_results) >= max_results:
        return ddg_results[:max_results]
    wiki_results = await web_search_wikipedia(query, max_results=max_results)
    seen = {r["url"] for r in ddg_results}
    for r in wiki_results:
        if r["url"] not in seen:
            ddg_results.append(r)
            seen.add(r["url"])
            if len(ddg_results) >= max_results:
                break
    return ddg_results[:max_results]


def _format_search_results(results: list[SearchHit], max_chars: int = 4000) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        t = (r.get("title") or "").strip()
        u = (r.get("url") or "").strip()
        s = (r.get("snippet") or "").strip()
        block = f"[{i}] {t}\nURL: {u}\n{s}"
        lines.append(block)
    joined = "\n\n".join(lines)
    return joined[:max_chars]


def _extract_search_marker(text: str) -> tuple[str | None, str]:
    if not text:
        return None, text
    m = re.match(r'^\s*!search\s+(.+?)(?:\n|$)', text)
    if m:
        return m.group(1).strip(), text[m.end():].lstrip()
    return None, text

# ============================================================
# CHART / INFOGRAPHIC ENGINE (Pillow)
# ============================================================
_PALETTE = [
    "#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#6366F1",
]

CHART_THEMES = {
    "dark_modern": {
        "bg": "#0E0E12", "bg_grad": ("#171728", "#0E0E12"),
        "text": "#F3F4F6", "text_dim": "#9CA3AF", "grid": "#2A2A3A",
        "accent": "#10B981", "card": "#16161E", "border": "#2A2A3A",
    },
    "light_minimal": {
        "bg": "#FAFAFB", "bg_grad": ("#FFFFFF", "#F1F1F4"),
        "text": "#111827", "text_dim": "#4B5563", "grid": "#E5E7EB",
        "accent": "#2563EB", "card": "#FFFFFF", "border": "#E5E7EB",
    },
    "ocean": {
        "bg": "#0A1929", "bg_grad": ("#103A5C", "#0A1929"),
        "text": "#E5F2FF", "text_dim": "#7FB1D6", "grid": "#17334B",
        "accent": "#3FB0FF", "card": "#0F2538", "border": "#17334B",
    },
    "retro": {
        "bg": "#FBF6E9", "bg_grad": ("#FFF8E7", "#F0E2B6"),
        "text": "#2D2B22", "text_dim": "#6B6350", "grid": "#D8CBA5",
        "accent": "#D97706", "card": "#FFFAEB", "border": "#D8CBA5",
    },
}


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = (h or "#000000").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return (0, 0, 0)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _as_rgb(c: Color) -> tuple[int, int, int]:
    if isinstance(c, str):
        return _hex_to_rgb(c)
    return (int(c[0]), int(c[1]), int(c[2]))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(c))) for c in rgb])


def _lerp_color(c1: Color, c2: Color, t: float) -> tuple[int, int, int]:
    r1, g1, b1 = _as_rgb(c1)
    r2, g2, b2 = _as_rgb(c2)
    return (
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


def _darken(c: Color, factor: float = 0.7) -> tuple[int, int, int]:
    rgb = _as_rgb(c)
    return (int(rgb[0] * factor), int(rgb[1] * factor), int(rgb[2] * factor))


def _lighten(c: Color, factor: float = 1.3) -> tuple[int, int, int]:
    rgb = _as_rgb(c)
    return (
        min(255, int(rgb[0] * factor)),
        min(255, int(rgb[1] * factor)),
        min(255, int(rgb[2] * factor)),
    )


def _make_gradient_bg(w: int, h: int, c1: str, c2: str) -> Image.Image:
    base = Image.new("RGB", (1, h), _hex_to_rgb(c1))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel((0, y), _lerp_color(c1, c2, t))
    return base.resize((w, h), Image.Resampling.BILINEAR)


def _load_font(size: int, bold: bool = False) -> Font:
    candidates_bold = [
        os.path.join("fonts", "Montserrat-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "arialbd.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    candidates_reg = [
        os.path.join("fonts", "Montserrat-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
        "arial.ttf",
        "DejaVuSans.ttf",
    ]
    candidates = candidates_bold if bold else candidates_reg
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: Font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text or " ", font=font)
    return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    xy_box: tuple[int, int, int, int],
    text: str,
    font: Font,
    fill: str | tuple[int, ...],
) -> None:
    x0, y0, x1, y1 = xy_box
    w, h = _text_size(draw, text, font)
    x = x0 + (x1 - x0 - w) // 2
    y = y0 + (y1 - y0 - h) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: Font, max_width: int) -> list[str]:
    words = (text or "").split()
    lines: list[str] = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        tw, _ = _text_size(draw, test, font)
        if tw <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _render_bar_chart(canvas: Image.Image, box: tuple[int, int, int, int],
                      spec: JsonDict, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    labels = [str(v) for v in spec.get("labels", [])]
    values = [float(v) for v in spec.get("values", []) if _is_number(v)]
    if not values:
        return
    colors = spec.get("colors") or _PALETTE
    # card
    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 24
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad
    font_title = _load_font(22, bold=True)
    font_lab = _load_font(13)
    font_val = _load_font(13, bold=True)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    # Chart area
    chart_top = cy0 + 4
    chart_bottom = cy1 - 36
    chart_left = cx0 + 8
    chart_right = cx1 - 8
    if chart_bottom <= chart_top:
        return

    vmax = max(values) if values else 1.0
    vmax = vmax if vmax > 0 else 1.0
    # nice ceiling
    magnitude = 10 ** int(math.floor(math.log10(vmax))) if vmax > 0 else 1
    nice_vmax = float(math.ceil(vmax / magnitude) * magnitude)
    if nice_vmax <= 0:
        nice_vmax = 1.0

    n = len(values)
    gap = 12
    total_w = chart_right - chart_left
    bar_w = max(6, int((total_w - gap * (n + 1)) / max(1, n)))

    # grid + axis labels
    steps = 5
    font_grid = _load_font(11)
    for i in range(steps + 1):
        yy = chart_bottom - int((chart_bottom - chart_top) * i / steps)
        val = nice_vmax * i / steps
        draw.line([(chart_left, yy), (chart_right, yy)], fill=theme["grid"], width=1)
        vs = f"{val:.2f}".rstrip("0").rstrip(".")
        draw.text((cx0 - 4 - _text_size(draw, vs, font_grid)[0], yy - 6), vs, font=font_grid, fill=theme["text_dim"])

    for idx, val in enumerate(values):
        bx = chart_left + gap + idx * (bar_w + gap)
        bh = int((chart_bottom - chart_top) * (val / nice_vmax))
        by = chart_bottom - bh
        color = colors[idx % len(colors)]
        try:
            rgb = _hex_to_rgb(color)
        except Exception:
            rgb = (79, 70, 229)
        # gradient bar
        bar_img = Image.new("RGB", (bar_w, max(1, bh)))
        for yy in range(max(1, bh)):
            t = yy / max(1, bh - 1)
            bar_img.putpixel((0, yy), _lerp_color(_lighten(rgb, 1.25), rgb, t))
        bar_img = bar_img.resize((bar_w, max(1, bh)), Image.Resampling.BILINEAR)
        if bh > 0:
            canvas.paste(bar_img, (bx, by))
        # value on top
        vs = f"{val:g}"
        vw, _ = _text_size(draw, vs, font_val)
        draw.text((bx + (bar_w - vw) // 2, by - 20), vs, font=font_val, fill=theme["text"])
        # label
        lab = labels[idx] if idx < len(labels) else ""
        lab = lab[:14]
        lw, _ = _text_size(draw, lab, font_lab)
        draw.text((bx + (bar_w - lw) // 2, chart_bottom + 8), lab, font=font_lab, fill=theme["text_dim"])


def _render_line_chart(canvas: Image.Image, box: tuple[int, int, int, int],
                       spec: JsonDict, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    xs = [str(v) for v in spec.get("x", [])]
    series = spec.get("series", []) or []
    if not series:
        return
    # normalize series
    norm_series: list[SeriesSpec] = []
    for s in series:
        if not isinstance(s, dict):
            continue
        series_item = cast(JsonDict, s)
        ys = [float(v) for v in s.get("y", []) if _is_number(v)]
        if not ys:
            continue
        raw_color = series_item.get("color")
        color = raw_color if isinstance(raw_color, str) else _PALETTE[len(norm_series) % len(_PALETTE)]
        raw_name = series_item.get("name")
        norm_series.append({
            "name": raw_name if isinstance(raw_name, str) and raw_name else f"Series {len(norm_series) + 1}",
            "y": ys,
            "color": color,
        })
    if not norm_series:
        return

    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 24
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad
    font_title = _load_font(22, bold=True)
    font_lab = _load_font(12)
    font_grid = _load_font(11)
    font_legend = _load_font(12)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    # legend at top-right
    legend_x = cx1
    legend_y = cy0 - 4
    for s in reversed(norm_series):
        name = str(s["name"])[:18]
        color = str(s["color"])
        tw, th = _text_size(draw, name, font_legend)
        legend_x -= tw + 24
        draw.line([(legend_x, legend_y + 8), (legend_x + 14, legend_y + 8)],
                  fill=_hex_to_rgb(color), width=3)
        draw.text((legend_x + 18, legend_y), name, font=font_legend, fill=theme["text_dim"])

    chart_top = cy0 + 8
    chart_bottom = cy1 - 30
    chart_left = cx0 + 6
    chart_right = cx1 - 6
    if chart_bottom <= chart_top:
        return

    all_ys = [v for s in norm_series for v in cast(list[float], s["y"])]
    vmin = min(all_ys)
    vmax = max(all_ys)
    if vmax == vmin:
        vmax = vmin + 1
    pad = (vmax - vmin) * 0.1
    vmin -= pad
    vmax += pad

    steps = 5
    for i in range(steps + 1):
        yy = chart_bottom - int((chart_bottom - chart_top) * i / steps)
        val = vmin + (vmax - vmin) * i / steps
        draw.line([(chart_left, yy), (chart_right, yy)], fill=theme["grid"], width=1)
        vs = f"{val:.2f}".rstrip("0").rstrip(".")
        draw.text((cx0 - 4 - _text_size(draw, vs, font_grid)[0], yy - 6),
                  vs, font=font_grid, fill=theme["text_dim"])

    # X positions
    max_len = max(len(cast(list[float], s["y"])) for s in norm_series)
    if max_len < 2:
        max_len = 2
    x_step = (chart_right - chart_left) / (max_len - 1)

    def _y_to_px(v: float) -> int:
        return chart_bottom - int((v - vmin) / (vmax - vmin) * (chart_bottom - chart_top))

    for s in norm_series:
        color = str(s["color"])
        pts = [(chart_left + i * x_step, _y_to_px(v)) for i, v in enumerate(cast(list[float], s["y"]))]
        if len(pts) >= 2:
            draw.line(pts, fill=_hex_to_rgb(color), width=3)
        for p in pts:
            r = 4
            draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r],
                         fill=_hex_to_rgb(color), outline=theme["bg"], width=2)

    # X labels
    for i in range(max_len):
        lab = xs[i] if i < len(xs) else str(i + 1)
        lab = lab[:10]
        lx = chart_left + i * x_step
        lw, _ = _text_size(draw, lab, font_lab)
        draw.text((lx - lw // 2, chart_bottom + 6), lab, font=font_lab, fill=theme["text_dim"])


def _render_pie_chart(canvas: Image.Image, box: tuple[int, int, int, int],
                      spec: JsonDict, theme: ChartTheme, depth: int = 0) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    labels = [str(v) for v in spec.get("labels", [])]
    values = [float(v) for v in spec.get("values", []) if _is_number(v)]
    if not values:
        return
    colors = spec.get("colors") or _PALETTE
    total = sum(values)
    if total <= 0:
        return

    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 24
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad

    font_title = _load_font(22, bold=True)
    font_legend = _load_font(13)
    font_pct = _load_font(13, bold=True)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    # Pie on left half, legend on right half
    chart_w = (cx1 - cx0)
    pie_box = (
        cx0 + 10,
        cy0 + 10,
        cx0 + min(chart_w // 2 + 40, (cy1 - cy0) + 10),
        cy1 - 10,
    )
    # make it square
    pw = pie_box[2] - pie_box[0]
    ph = pie_box[3] - pie_box[1]
    side = min(pw, ph)
    pcx = pie_box[0] + pw // 2
    pcy = pie_box[1] + ph // 2
    px0 = pcx - side // 2
    py0 = pcy - side // 2
    px1 = px0 + side
    py1 = py0 + side

    start = -90.0
    legend_x = px1 + 30
    legend_y = cy0 + 20

    for idx, val in enumerate(values):
        extent = 360 * (val / total)
        color = colors[idx % len(colors)]
        try:
            rgb = _hex_to_rgb(str(color))
        except Exception:
            rgb = _hex_to_rgb(_PALETTE[idx % len(_PALETTE)])

        if depth > 0:
            # Draw "side wall"
            for d in range(depth, 0, -1):
                draw.pieslice([px0, py0 + d, px1, py1 + d],
                              start, start + extent,
                              fill=_darken(rgb, 0.55), outline=_darken(rgb, 0.5))
        draw.pieslice([px0, py0, px1, py1], start, start + extent,
                      fill=rgb, outline=theme["bg"], width=2)
        start += extent

    # Legend
    for idx, val in enumerate(values):
        color = colors[idx % len(colors)]
        try:
            rgb = _hex_to_rgb(str(color))
        except Exception:
            rgb = _hex_to_rgb(_PALETTE[idx % len(_PALETTE)])
        pct = val / total * 100
        lab = labels[idx] if idx < len(labels) else f"Item {idx + 1}"
        lab_line = f"{lab}"
        pct_line = f"{pct:.1f}%"
        # swatch
        draw.rectangle([legend_x, legend_y + 4, legend_x + 16, legend_y + 20], fill=rgb)
        draw.text((legend_x + 24, legend_y), lab_line[:28], font=font_legend, fill=theme["text"])
        pw_, _ = _text_size(draw, pct_line, font_pct)
        draw.text((cx1 - pw_ - 4, legend_y), pct_line, font=font_pct, fill=theme["text_dim"])
        legend_y += 28
        if legend_y > cy1 - 20:
            break


def _render_table(canvas: Image.Image, box: tuple[int, int, int, int],
                  spec: JsonDict, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    headers = [str(h) for h in spec.get("headers", [])]
    rows = [[str(c) for c in row] for row in spec.get("rows", [])]
    if not headers and not rows:
        return

    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 20
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad

    font_title = _load_font(22, bold=True)
    font_head = _load_font(14, bold=True)
    font_row = _load_font(14)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    n_cols = max([len(headers)] + [len(r) for r in rows] + [1])
    col_w = (cx1 - cx0) // n_cols
    row_h = 30

    y_cur = cy0 + 4
    # header
    if headers:
        for i in range(n_cols):
            label = headers[i] if i < len(headers) else ""
            cell_x0 = cx0 + i * col_w
            cell_x1 = cell_x0 + col_w
            draw.rectangle([cell_x0, y_cur, cell_x1, y_cur + row_h],
                           fill=theme["accent"])
            _draw_centered_text(draw, (cell_x0 + 6, y_cur, cell_x1 - 6, y_cur + row_h),
                                label, font_head, "#FFFFFF")
        y_cur += row_h

    # rows
    for r_i, r in enumerate(rows):
        if y_cur + row_h > cy1:
            break
        row_bg = theme["bg"] if r_i % 2 == 0 else theme["card"]
        draw.rectangle([cx0, y_cur, cx1, y_cur + row_h], fill=row_bg)
        for i in range(n_cols):
            cell = r[i] if i < len(r) else ""
            cell_x0 = cx0 + i * col_w
            cell_x1 = cell_x0 + col_w
            _draw_centered_text(draw, (cell_x0 + 6, y_cur, cell_x1 - 6, y_cur + row_h),
                                cell[:40], font_row, theme["text"])
        draw.line([(cx0, y_cur + row_h), (cx1, y_cur + row_h)], fill=theme["grid"], width=1)
        y_cur += row_h


async def _load_remote_image(url: str) -> Image.Image | None:
    try:
        data = await download_image_bytes(url)
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception as e:
        logger.warning(f"load_remote_image err: {e}")
        return None


def _render_image_block(canvas: Image.Image, box: tuple[int, int, int, int],
                        img: Image.Image, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 12
    ix0, iy0, ix1, iy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad
    box_w = ix1 - ix0
    box_h = iy1 - iy0
    if box_w <= 0 or box_h <= 0:
        return
    im = img.copy()
    im.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
    ox = ix0 + (box_w - im.width) // 2
    oy = iy0 + (box_h - im.height) // 2
    if im.mode == "RGBA":
        canvas.paste(im, (ox, oy), im)
    else:
        canvas.paste(im, (ox, oy))


def _is_number(x: object) -> bool:
    try:
        float(cast(Any, x))
        return True
    except (TypeError, ValueError):
        return False


async def render_infographic(spec: JsonDict, user_images: list[bytes] | None = None) -> BytesIO:
    """
    Строит инфографику по спецификации.
    spec = {
        "theme": "dark_modern",
        "title": "...",
        "subtitle": "...",
        "width": 1400,
        "blocks": [ {...}, ... ]
    }
    Возвращает BytesIO с PNG.
    """
    theme_name = spec.get("theme", "dark_modern")
    theme = CHART_THEMES.get(theme_name, CHART_THEMES["dark_modern"])

    width = int(spec.get("width", 1400))
    title = spec.get("title") or ""
    subtitle = spec.get("subtitle") or ""
    blocks = spec.get("blocks", []) or []

    # Preload images (URL or user references)
    preloaded: dict[int, Image.Image] = {}
    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "image":
            src = block.get("source", "url")
            if src == "user" and user_images:
                i = int(block.get("index", 0))
                if 0 <= i < len(user_images):
                    try:
                        preloaded[idx] = Image.open(BytesIO(user_images[i])).convert("RGBA")
                    except Exception:
                        pass
            elif src == "url" and block.get("url"):
                img = await _load_remote_image(block["url"])
                if img is not None:
                    preloaded[idx] = img

    # Precompute heights
    # Approximate: heading 60, text computed by width, divider 32, chart uses "height" or default 340,
    # table uses headers/rows, image uses "height" or 400.
    padding = 40
    inner_w = width - padding * 2

    # measure text heights
    tmp_img = Image.new("RGB", (10, 10))
    tmp_draw = ImageDraw.Draw(tmp_img)
    font_title = _load_font(44, bold=True)
    font_sub = _load_font(20)
    font_h = _load_font(28, bold=True)
    font_text = _load_font(18)

    heights: list[int] = []
    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            heights.append(0)
            continue
        t = block.get("type", "text")
        if t == "heading":
            heights.append(52)
        elif t == "text":
            lines = _wrap_lines(tmp_draw, block.get("text", ""), font_text, inner_w)
            heights.append(max(30, len(lines) * 26 + 8))
        elif t == "divider":
            heights.append(36)
        elif t == "bar":
            heights.append(int(block.get("height", 340)))
        elif t == "line":
            heights.append(int(block.get("height", 340)))
        elif t == "pie":
            heights.append(int(block.get("height", 360)))
        elif t == "pie3d":
            heights.append(int(block.get("height", 380)))
        elif t == "table":
            n_rows = len(block.get("rows", []))
            n_head = 1 if block.get("headers") else 0
            heights.append(70 + (n_rows + n_head) * 30)
        elif t == "image":
            heights.append(int(block.get("height", 400)))
        else:
            heights.append(0)

    header_h = 0
    if title:
        header_h += 66
    if subtitle:
        header_h += 34

    total_h = padding * 2 + header_h + sum(heights) + max(0, len(blocks) - 1) * 20
    total_h = max(600, total_h)

    # Draw background
    bg_grad = theme.get("bg_grad")
    if isinstance(bg_grad, (tuple, list)) and len(bg_grad) >= 2:
        bg_c1, bg_c2 = str(bg_grad[0]), str(bg_grad[1])
    else:
        bg_c1 = bg_c2 = _theme_str(theme, "bg")
    canvas = _make_gradient_bg(width, total_h, bg_c1, bg_c2).convert("RGBA")

    draw = ImageDraw.Draw(canvas)

    # Title
    y = padding
    if title:
        draw.text((padding, y), title, font=font_title, fill=_theme_str(theme, "text"))
        y += 58
    if subtitle:
        draw.text((padding, y), subtitle, font=font_sub, fill=_theme_str(theme, "text_dim"))
        y += 34
    if title or subtitle:
        # subtle divider
        draw.line([(padding, y), (width - padding, y)], fill=_theme_str(theme, "border"), width=2)
        y += 8

    # Blocks
    for idx, block in enumerate(blocks):
        h = heights[idx]
        if h <= 0 or not isinstance(block, dict):
            continue
        box = (padding, y, width - padding, y + h)
        t = block.get("type", "text")

        if t == "heading":
            _draw_centered_text(draw, (box[0], box[1], box[2], box[1] + h),
                                str(block.get("text", "")), font_h, _theme_str(theme, "text"))
        elif t == "text":
            lines = _wrap_lines(draw, block.get("text", ""), font_text, inner_w)
            ty = y
            for line in lines:
                draw.text((padding, ty), line, font=font_text, fill=_theme_str(theme, "text"))
                ty += 26
        elif t == "divider":
            mid_y = y + h // 2
            draw.line([(padding + 20, mid_y), (width - padding - 20, mid_y)],
                      fill=_theme_str(theme, "border"), width=2)
        elif t == "bar":
            _render_bar_chart(canvas, box, block, theme)
        elif t == "line":
            _render_line_chart(canvas, box, block, theme)
        elif t == "pie":
            _render_pie_chart(canvas, box, block, theme, depth=0)
        elif t == "pie3d":
            _render_pie_chart(canvas, box, block, theme, depth=max(12, h // 20))
        elif t == "table":
            _render_table(canvas, box, block, theme)
        elif t == "image":
            img = preloaded.get(idx)
            if img is not None:
                _render_image_block(canvas, box, img, theme)

        y += h + 20

    out = BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True)
    out.seek(0)
    return out


def _extract_chart_marker(text: str) -> tuple[JsonDict | None, str]:
    if not text or "!chart" not in text:
        return None, text
    # try fenced first
    m = re.search(r'!chart\s*\n?```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if not m:
        # bare json (greedy balanced)
        idx = text.find("!chart")
        if idx >= 0:
            start = text.find("{", idx)
            if start >= 0:
                depth = 0
                end = -1
                in_str = False
                esc = False
                for i in range(start, len(text)):
                    c = text[i]
                    if esc:
                        esc = False
                        continue
                    if c == "\\":
                        esc = True
                        continue
                    if c == '"':
                        in_str = not in_str
                        continue
                    if in_str:
                        continue
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                if end > 0:
                    raw = text[start:end]
                    try:
                        spec = _json_dict(json.loads(raw))
                        remaining = (text[:idx] + text[end:]).strip()
                        return spec, remaining
                    except Exception:
                        pass
        return None, text
    try:
        spec = _json_dict(json.loads(m.group(1)))
        remaining = (text[:m.start()] + text[m.end():]).strip()
        return spec, remaining
    except Exception as e:
        logger.warning(f"chart json parse fail: {e}")
        return None, text

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


def resolve_avatar_target_tg(message: telebot.types.Message) -> telebot.types.User | None:
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


async def get_avatar_description_tg(
    message: telebot.types.Message, chat_id: int, user_id: int, lang: str = "ru",
) -> str | None:
    target = resolve_avatar_target_tg(message)
    if target is None:
        return None
    name = target.full_name or ("человек" if lang == "ru" else "user")
    uname = f"@{target.username}" if target.username else ""
    try:
        photos = await tg_bot.get_user_profile_photos(target.id, limit=1)
    except Exception as e:
        logger.warning(f"avatar fetch: {e}")
        return None
    if not (photos.total_count > 0 and photos.photos):
        return _t(lang, "avatar_none", name)
    try:
        file_id = photos.photos[0][-1].file_id
        img_bytes = await get_tg_file_bytes(tg_bot, file_id)
        prompt = (
            f"Ты только что посмотрел аватарку пользователя {name} {uname}. "
            f"Опиши коротко (1-2 предложения) в стиле Кульша. Без markdown. "
            f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
            if lang == "ru" else
            f"You've just seen the avatar of {name} {uname}. "
            f"Describe briefly (1-2 sentences) in Kulsh's style. No markdown. "
            f"Do NOT use markers !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
        )
        return _json_str(await ask_ai_async(
            prompt=prompt, image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id, platform="tg",
        )) or None
    except Exception as e:
        logger.warning(f"avatar desc: {e}")
        return None


async def get_avatar_description_ds(
    message: discord.Message, chat_id: int, user_id: int, lang: str = "ru",
) -> str | None:
    target = None
    me = _ds_user(ds_bot)
    if message.mentions:
        for m in message.mentions:
            if m.id != me.id:
                target = m
                break
    if target is None and message.reference and message.reference.resolved and isinstance(message.reference.resolved, discord.Message):
        ref_auth = message.reference.resolved.author
        if ref_auth.id != me.id:
            target = ref_auth
    if target is None and message.author.id != me.id:
        target = message.author
    if target is None:
        return None
    name = target.display_name
    try:
        img_bytes = await download_image_bytes(target.display_avatar.url)
        prompt = (
            f"Ты только что посмотрел аватарку пользователя {name}. "
            f"Опиши коротко (1-2 предложения) в стиле Кульша. Без markdown. "
            f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
            if lang == "ru" else
            f"You've just seen the avatar of {name}. "
            f"Describe briefly (1-2 sentences) in Kulsh's style. No markdown. "
            f"Do NOT use markers !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
        )
        desc = _json_str(await ask_ai_async(
            prompt=prompt, image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id, platform="ds",
        ))
        return desc or None
    except Exception as e:
        logger.warning(f"DS avatar desc: {e}")
        return None


async def get_recall_media_description_tg(
    message: telebot.types.Message, chat_id: int, user_id: int, n: int = 3, lang: str = "ru",
) -> str | None:
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
            prompt = (
                f"Ты вспоминаешь недавние медиа. Список:\n{meta}\n\n"
                f"Коротко прокомментируй в стиле Кульша. Без markdown. "
                f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
                if lang == "ru" else
                f"You recall recent media. List:\n{meta}\n\n"
                f"Comment briefly in Kulsh's style. No markdown. "
                f"Do NOT use markers !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
            )
            return _json_str(await ask_ai_async(
                prompt=prompt, chat_id=chat_id, user_id=user_id, platform="tg",
            )) or None
        except Exception as e:
            logger.warning(f"recall meta: {e}")
            return None
    try:
        prompt = (
            "Ты вспоминаешь последнее медиа. Опиши коротко в стиле Кульша. Без markdown. "
            "НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
            if lang == "ru" else
            "You recall the last media. Describe briefly in Kulsh's style. No markdown. "
            "Do NOT use markers !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
        )
        return _json_str(await ask_ai_async(
            prompt=prompt, image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id, platform="tg",
        )) or None
    except Exception as e:
        logger.warning(f"recall image: {e}")
        return None

# ============================================================
# LOOKSMAXXING TIERS
# ============================================================
TIER_DISTRIBUTION: list[dict[str, str | float]] = [
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
        candidates = [str(t["key"]).upper(), str(t["short"]).upper(), str(t["full_m"]).upper(), str(t["full_f"]).upper()]
        if tn in candidates or tn.replace(" ", "") in [c.replace(" ", "") for c in candidates]:
            return str(t["key"])
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
# INFOGRAPHIC (looksmaxxing) — существующий
# ============================================================
def load_font(size: int) -> Font:
    font_path = os.path.join("fonts", "Montserrat-Bold.ttf")
    try:
        return ImageFont.truetype(font_path, size)
    except IOError:
        return ImageFont.load_default()


def add_bullet(text: str) -> str:
    if text.startswith("•") or text.startswith("-"):
        return text
    return f"• {text}"


def _wrap_text(text: str, draw: ImageDraw.ImageDraw, font: Font, max_width: int) -> list[str]:
    words = text.split(' ')
    lines: list[str] = []
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


def _block_height(lines: list[str], font: Font, line_spacing: int, draw: ImageDraw.ImageDraw) -> int:
    total = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total += int(bbox[3] - bbox[1]) + line_spacing
    if total > 0:
        total -= line_spacing
    return total


async def create_infographic(photo_bytes: bytes, data: JsonDict, theme: str = "dark", lang: str = "en") -> BytesIO:
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
            if float(t["psl_low"]) <= psl_val <= float(t["psl_high"]):
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
        low = float(tier["psl_low"])
        high = float(tier["psl_high"])
        tier_key = str(tier["key"])
        tier_short = str(tier["short"])
        x_start = chart_x + (low - 1.0) / total_range * chart_width
        x_end = chart_x + (high - 1.0) / total_range * chart_width
        draw.rectangle((x_start, chart_y, x_end, chart_y + chart_height), fill=get_tier_color(tier_key))
        if tier_key == str(TIER_DISTRIBUTION[current_tier_idx]["key"]):
            draw.rectangle([x_start - 1, chart_y - 1, x_end + 1, chart_y + chart_height + 1],
                           outline=highlight_outline, width=2)
        tb = draw.textbbox((0, 0), tier_short, font=font_tier_label)
        tw = tb[2] - tb[0]
        draw.text(((x_start + x_end) / 2 - tw / 2, chart_y + chart_height + 4),
                  tier_short, fill=text_secondary, font=font_tier_label)
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
    current_y = float(psl_bar_y + psl_bar_h + 25)
    for key, val_str in metrics_mapping:
        title = METRIC_NAMES.get(key, key)
        tb = draw.textbbox((0, 0), title, font=font_text)
        title_h = tb[3] - tb[1]
        val_lines = _wrap_text(str(val_str), draw, font_text, col2_width)
        val_block_h = _block_height(val_lines, font_text, line_spacing, draw)
        row_height = max(base_row_height, title_h + 2 * min_padding, val_block_h + 2 * min_padding)
        draw.line([(col1_x, current_y), (right_margin, current_y)], fill=line_color, width=1)
        draw.text((col1_x, current_y + (row_height - title_h) / 2), title, fill=text_secondary, font=font_text)
        val_y = float(current_y) + (row_height - val_block_h) / 2
        for line in val_lines:
            bbox = draw.textbbox((0, 0), line, font=font_text)
            lh = bbox[3] - bbox[1]
            draw.text((col2_x, val_y), line, fill=text_primary, font=font_text)
            val_y += float(lh) + line_spacing
        current_y += float(row_height)
    draw.line([(col1_x, current_y), (right_margin, current_y)], fill=line_color, width=1)

    raw_pros = data.get("pros", [])
    raw_cons = data.get("cons", [])
    if isinstance(raw_pros, str):
        raw_pros = [raw_pros]
    if isinstance(raw_cons, str):
        raw_cons = [raw_cons]
    pros = [add_bullet(str(p)) for p in raw_pros] if isinstance(raw_pros, list) else []
    cons = [add_bullet(str(c)) for c in raw_cons] if isinstance(raw_cons, list) else []
    col_y = current_y + 20
    draw.text((start_x, col_y), STRENGTHS, fill=accent, font=font_sub)
    draw.text((start_x + 220, col_y), WEAKNESSES, fill=weak_color, font=font_sub)
    col_width = 200
    line_height = 26
    list_start_y = col_y + 38

    def render_list(items: list[str], x: int, y: int, color: str, max_width: int = col_width) -> int:
        cy = y
        for item in items:
            for line in _wrap_text(item, draw, list_font, max_width):
                draw.text((x, cy), line, fill=color, font=list_font)
                cy += line_height
            cy += 4
        return cy

    end_left = render_list(pros, start_x + 10, int(list_start_y), text_primary)
    end_right = render_list(cons, start_x + 230, int(list_start_y), text_primary)
    max_y = max(end_left, end_right)
    draw.text((40, max_y + 30), FULL_ANALYSIS, fill=text_tertiary, font=font_small)
    out = BytesIO()
    image.save(out, format="PNG")
    out.seek(0)
    return out


async def create_battle_infographic(
    p1: bytes, p2: bytes, data: JsonDict, theme: str = "dark", lang: str = "en",
) -> BytesIO:
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

    def paste_rounded(img_bytes: bytes, x: int, y: int, w: int, h: int, radius: int = 28) -> tuple[int, int, int, int]:
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
        return _json_dict(json.loads(clean_json_text(raw)))
    except json.JSONDecodeError:
        logger.error(f"Looksmaxxing JSON decode: {raw[:200]}")
        return {"error": _t(lang, "ai_json_fail")}


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
        return _json_dict(json.loads(clean_json_text(raw)))
    except json.JSONDecodeError:
        logger.error(f"Battle JSON decode: {raw[:200]}")
        return {"error": _t(lang, "ai_json_fail")}

# ============================================================
# STYLED BUTTON
# ============================================================
class StyledButton(InlineKeyboardButton):
    def __init__(self, text: str, style: str | None = None, **kwargs: Any) -> None:
        super().__init__(text, **kwargs)
        self.style = style

    def to_dict(self) -> JsonDict:
        d = _json_dict(cast(Any, super()).to_dict())
        if self.style:
            d['style'] = self.style
        return d


def btn(text: str, style: str | None = None, **kwargs: Any) -> StyledButton:
    return StyledButton(text, style=style, **kwargs)


def _mini_app_button(lang: str, is_private: bool) -> StyledButton:
    text = _t(lang, "btn_open_mini")
    if is_private:
        return btn(text, style="primary", web_app=WebAppInfo(url=MINI_APP_URL))
    return btn(text, style="primary", url=MINI_APP_URL)

# ============================================================
# CONFIG TEXT / KEYBOARDS
# ============================================================
def _config_text(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    prompt_safe = html.escape(cfg.get("custom_prompt") or _t(lang, "cfg_prompt_default"))
    line = "═" * 22
    on = "✅"
    off = "❌"
    theme_disp = _t(lang, "dark") if cfg.get("theme", "dark") == "dark" else _t(lang, "light")
    credits = get_user_credits(platform, user_id)
    stream_txt = f"{on if cfg.get('streaming_enabled') else off} · {'premium' if premium_functions_enabled else 'off'}"
    search_txt = on if cfg.get("web_search_enabled", True) else off
    return (
        f"✦ {_t(lang, 'cfg_title')} ✦\n{line}\n"
        f"{_t(lang, 'cfg_lang')}: {_t(lang, 'russian') if lang == 'ru' else _t(lang, 'english')}\n"
        f"{_t(lang, 'cfg_theme')}: {theme_disp}\n"
        f"{_t(lang, 'cfg_model')}: {model_display_name(cfg.get('model'), lang)}\n"
        f"{_t(lang, 'cfg_temp_short')}: <code>{cfg.get('temperature', 0.9)}</code>\n"
        f"{_t(lang, 'cfg_sep')}: {on if cfg.get('separate_enabled', True) else off}\n"
        f"{_t(lang, 'cfg_stream')}: {stream_txt}\n"
        f"{_t(lang, 'cfg_stickers')}: {on if cfg.get('stickers_enabled', True) else off}\n"
        f"{_t(lang, 'cfg_autoreply')}: {on if cfg.get('random_reply_enabled') else off}\n"
        f"{_t(lang, 'cfg_random')}: {on if cfg.get('random_messages_enabled', True) else off}\n"
        f"{_t(lang, 'cfg_websearch')}: {search_txt}\n"
        f"{_t(lang, 'cfg_credits_label')}: <code>{credits}/{DAILY_CREDITS}</code>\n"
        f"{line}\n"
        f"{_t(lang, 'cfg_prompt_label')}: {prompt_safe}"
    )


def build_main_config_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn(_t(lang, "cfg_lang"), style=None, callback_data="cfg:lang"),
        btn(_t(lang, "cfg_theme"), style=None, callback_data="cfg:theme"),
    )
    kb.row(
        btn(f"{_t(lang, 'cfg_model')}: {model_display_name(cfg.get('model'), lang)}",
            style="primary", callback_data="cfg:model"),
        btn(f"{_t(lang, 'cfg_temp_short')}: {cfg.get('temperature', 0.9)}",
            style=None, callback_data="cfg:temp"),
    )
    kb.row(
        btn(f"{_t(lang, 'cfg_sep')}: {'✅' if cfg.get('separate_enabled', True) else '❌'}",
            style=None, callback_data="cfg:separate"),
        btn(f"{_t(lang, 'cfg_stream')}: {'✅' if cfg.get('streaming_enabled') else '❌'}",
            style=None, callback_data="cfg:streaming"),
    )
    kb.row(
        btn(f"{_t(lang, 'cfg_stickers')}: {'✅' if cfg.get('stickers_enabled', True) else '❌'}",
            style=None, callback_data="cfg:stickers"),
        btn(f"{_t(lang, 'cfg_autoreply')}: {'✅' if cfg.get('random_reply_enabled') else '❌'}",
            style=None, callback_data="cfg:autoreply"),
    )
    kb.row(
        btn(f"{_t(lang, 'cfg_random')}: {'✅' if cfg.get('random_messages_enabled', True) else '❌'}",
            style=None, callback_data="cfg:random"),
        btn(f"{_t(lang, 'cfg_websearch')}: {'✅' if cfg.get('web_search_enabled', True) else '❌'}",
            style=None, callback_data="cfg:websearch"),
    )
    kb.row(
        btn(_t(lang, "cfg_edit_prompt"), style="primary", callback_data="cfg:prompt"),
    )
    kb.row(
        btn(_t(lang, "cfg_reset_memory"), style="danger", callback_data="cfg:reset_memory"),
        btn(_t(lang, "cfg_reset_prompt"), style="danger", callback_data="cfg:reset_prompt"),
    )
    kb.row(
        btn(_t(lang, "cfg_apply_close"), style="success", callback_data="cfg:apply")
    )
    return kb


def build_model_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    cur = cfg.get("model")
    kb = InlineKeyboardMarkup()
    auto_mark = "🔘" if not cur else "▫️"
    kb.row(btn(f"{auto_mark} {_t(lang, 'cfg_auto')}", style=None, callback_data="cfg:model_set:auto"))
    row: list[StyledButton] = []
    for idx, model in enumerate(MODEL_LIST):
        mark = "🔘" if cur == model else "▫️"
        row.append(btn(f"{mark} {MODEL_DISPLAY.get(model, model)}", style=None, callback_data=f"cfg:model_set:{idx}"))
        if len(row) == 2:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    kb.row(btn(_t(lang, "cfg_back"), style="primary", callback_data="cfg:model_back"))
    return kb


def build_lang_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    cur = cfg.get("language", "ru")
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn(f"{'🔘' if cur == 'ru' else '▫️'} Русский 🇷🇺",
            style="primary" if cur == "ru" else None, callback_data="cfg:lang_set:ru"),
        btn(f"{'🔘' if cur == 'en' else '▫️'} English 🇬🇧",
            style="primary" if cur == "en" else None, callback_data="cfg:lang_set:en"),
    )
    kb.row(btn(_t(lang, "cfg_back_slash"), style="primary", callback_data="cfg:sub_back"))
    return kb


def build_theme_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    cur = cfg.get("theme", "dark")
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    kb.row(
        btn(f"{'🔘' if cur == 'dark' else '▫️'} {'Тёмная 🌑' if lang == 'ru' else 'Dark 🌑'}",
            style="primary" if cur == "dark" else None, callback_data="cfg:theme_set:dark"),
        btn(f"{'🔘' if cur == 'light' else '▫️'} {'Светлая ☀️' if lang == 'ru' else 'Light ☀️'}",
            style="primary" if cur == "light" else None, callback_data="cfg:theme_set:light"),
    )
    kb.row(btn(_t(lang, "cfg_back_slash"), style="primary", callback_data="cfg:sub_back"))
    return kb


def build_temp_keyboard(platform: str, chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user_config(platform, chat_id, user_id)
    cur = cfg.get("temperature", 0.9)
    lang = cfg.get("language", "ru")
    kb = InlineKeyboardMarkup()
    values = [0.2, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
    row: list[StyledButton] = []
    for v in values:
        mark = "🔘" if abs(cur - v) < 0.01 else "▫️"
        row.append(btn(f"{mark} {v}", style=None, callback_data=f"cfg:temp_set:{v}"))
    kb.row(*row[:4])
    kb.row(*row[4:])
    kb.row(btn(_t(lang, "cfg_back_slash"), style="primary", callback_data="cfg:sub_back"))
    return kb


def _model_picker_text(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    lang = cfg.get("language", "ru")
    return (
        f"<b>{_t(lang, 'cfg_choose_model')}</b>\n"
        f"{'─' * 22}\n"
        f"{_t(lang, 'cfg_current')}: {model_display_name(cfg.get('model'), lang)}\n\n"
        f"<b>{_t(lang, 'cfg_auto')}</b> — {_t(lang, 'cfg_auto_hint')}"
    )

# ============================================================
# МЕНЮ / START / HELP / DONATE (без GIF, с декором)
# ============================================================
def _build_menu_text(lang: str) -> str:
    return (
        "|K|*U*|L|*S*|H|\n\n"
        f"# {_t(lang, 'menu_title')}\n\n"
        f"✦彡巛〢 ✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"{_t(lang, 'menu_intro')}\n\n"
        f"**{_t(lang, 'menu_available')}**\n"
        f"▸ {_t(lang, 'menu_mini_app')}\n"
        f"▸ {_t(lang, 'menu_settings_item')}\n"
        f"▸ {_t(lang, 'menu_commands')}\n"
        f"▸ {_t(lang, 'menu_donate_item')}\n"
        f"▸ {_t(lang, 'menu_github_item')}\n\n"
        f"✦ 彡 巛 〢 〢 巛 彡 ✦"
    )


def _build_start_text(lang: str) -> str:
    return (
        f"# {_t(lang, 'start_title')}\n\n"
        f"✦彡巛〢 ✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"{_t(lang, 'start_intro')}\n\n"
        f"**{_t(lang, 'start_where')}**\n"
        f"▸ {_t(lang, 'start_mini_app')}\n"
        f"▸ {_t(lang, 'start_menu')}\n"
        f"▸ {_t(lang, 'start_config')}\n\n"
        f"🍷🗿 {MINI_APP_URL}"
    )


def build_menu_keyboard(lang: str, is_private: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(_mini_app_button(lang, is_private))
    kb.row(
        btn(_t(lang, "btn_settings"), style="success", callback_data="menu:settings"),
        btn(_t(lang, "btn_commands"), style=None, callback_data="menu:help"),
    )
    kb.row(
        btn(_t(lang, "btn_donate"), style=None, url=DONATE_URL),
        btn(_t(lang, "btn_github"), style=None, url=GITHUB_URL),
    )
    kb.row(
        btn(_t(lang, "btn_close"), style="danger", callback_data="menu:close")
    )
    return kb


def build_start_keyboard(lang: str, is_private: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(_mini_app_button(lang, is_private))
    kb.row(
        btn(_t(lang, "btn_menu"), style="success", callback_data="menu:open"),
        btn(_t(lang, "btn_settings"), style=None, callback_data="menu:settings"),
    )
    kb.row(
        btn(_t(lang, "btn_donate"), style=None, url=DONATE_URL),
        btn(_t(lang, "btn_github"), style=None, url=GITHUB_URL),
    )
    return kb

# ============================================================
# CALLBACK HANDLER (cfg:)
# ============================================================
async def _edit_or_send(call: telebot.types.CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    msg = _tg_msg(call)
    try:
        await tg_bot.edit_message_text(
            text, msg.chat.id, msg.message_id,
            parse_mode='HTML', reply_markup=kb,
        )
    except Exception as e:
        logger.warning(f"edit_message_text fail: {e}")


@_typed_decorator(tg_bot.callback_query_handler)(func=lambda call: bool(call.data and call.data.startswith("cfg:")))
async def handle_cfg_callback(call: telebot.types.CallbackQuery) -> None:
    msg = _tg_msg(call)
    data = call.data or ""
    owner = config_msg_owners.get(msg.message_id)
    if owner is not None and owner != call.from_user.id:
        l = get_user_config("tg", msg.chat.id, call.from_user.id).get("language", "ru")
        await tg_bot.answer_callback_query(_cb_id(call), _t(l, "cfg_not_yours"), show_alert=False)
        return

    chat_id = msg.chat.id
    user_id = call.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    toast = _t(lang, "cfg_updated")

    if action == "model_set":
        value = parts[2] if len(parts) > 2 else "auto"
        if value == "auto":
            cfg["model"] = None
            toast = _t(lang, "cfg_model_auto")
        else:
            try:
                idx = int(value)
                if 0 <= idx < len(MODEL_LIST):
                    cfg["model"] = MODEL_LIST[idx]
                    toast = _t(lang, "cfg_model_set", MODEL_DISPLAY.get(MODEL_LIST[idx], MODEL_LIST[idx]))
            except ValueError:
                pass
        await _edit_or_send(call, _model_picker_text("tg", chat_id, user_id),
                            build_model_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call), toast)
        return

    if action == "model":
        await _edit_or_send(call, _model_picker_text("tg", chat_id, user_id),
                            build_model_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action in ("model_back", "sub_back"):
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "lang":
        await _edit_or_send(call, f"<b>{_t(lang, 'cfg_lang')}</b>", build_lang_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "lang_set":
        val = parts[2] if len(parts) > 2 else "ru"
        if val in ("ru", "en"):
            cfg["language"] = val
            lang = val
            toast = _t(lang, "cfg_lang_set_ru") if val == "ru" else _t(lang, "cfg_lang_set_en")
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call), toast)
        return

    if action == "theme":
        await _edit_or_send(call, f"<b>{_t(lang, 'cfg_theme')}</b>", build_theme_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "theme_set":
        val = parts[2] if len(parts) > 2 else "dark"
        if val in ("dark", "light"):
            cfg["theme"] = val
            toast = _t(lang, "cfg_theme_dark") if val == "dark" else _t(lang, "cfg_theme_light")
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call), toast)
        return

    if action == "temp":
        await _edit_or_send(call, f"<b>{_t(lang, 'cfg_temp_short')}</b>",
                            build_temp_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "temp_set":
        try:
            temp_val = max(0.0, min(2.0, float(parts[2])))
            cfg["temperature"] = temp_val
            toast = _t(lang, "cfg_temp", temp_val)
        except (ValueError, IndexError):
            pass
        await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(_cb_id(call), toast)
        return

    if action == "prompt":
        try:
            sent = await tg_bot.send_message(
                chat_id, _t(lang, "cfg_edit_prompt_ask"),
                parse_mode='HTML',
                reply_markup=ForceReply(selective=True),
                reply_to_message_id=msg.message_id,
            )
            prompt_waiting[user_id] = sent.message_id
            key = (chat_id, user_id)
            config_children_msgs.setdefault(key, []).append(sent.message_id)
        except Exception as e:
            logger.warning(f"prompt ask fail: {e}")
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "apply":
        config_msg_owners.pop(msg.message_id, None)
        chat_key = get_chat_key("tg", chat_id)
        trig_id = config_trigger_msgs.pop(chat_key, None)
        if trig_id:
            try:
                await tg_bot.delete_message(chat_id, trig_id)
            except Exception:
                pass
        await _cleanup_config_children(chat_id, user_id)
        await tg_bot.answer_callback_query(_cb_id(call), _t(lang, "cfg_done"))
        asyncio.create_task(play_apply_animation(chat_id, msg.message_id))
        return

    if action == "separate":
        new_val = not cfg.get("separate_enabled", True)
        if new_val and cfg.get("streaming_enabled", False):
            await tg_bot.answer_callback_query(_cb_id(call), _t(lang, "cfg_mutex"), show_alert=False)
            return
        cfg["separate_enabled"] = new_val
    elif action == "streaming":
        if not premium_functions_enabled:
            await tg_bot.answer_callback_query(_cb_id(call), _t(lang, "cfg_premium_off"), show_alert=False)
            return
        new_val = not cfg.get("streaming_enabled", False)
        if new_val and cfg.get("separate_enabled", True):
            await tg_bot.answer_callback_query(_cb_id(call), _t(lang, "cfg_mutex"), show_alert=False)
            return
        cfg["streaming_enabled"] = new_val
    elif action == "stickers":
        cfg["stickers_enabled"] = not cfg.get("stickers_enabled", True)
    elif action == "autoreply":
        cfg["random_reply_enabled"] = not cfg.get("random_reply_enabled", False)
    elif action == "random":
        cfg["random_messages_enabled"] = not cfg.get("random_messages_enabled", True)
    elif action == "websearch":
        cfg["web_search_enabled"] = not cfg.get("web_search_enabled", True)
    elif action == "reset_prompt":
        cfg["custom_prompt"] = None
        toast = _t(lang, "cfg_prompt_reset")
    elif action == "reset_memory":
        chat_key = f"tg_{chat_id}"
        if chat_key in long_term_memory:
            del long_term_memory[chat_key]
            save_long_term_memory(long_term_memory)
        chat_memories[chat_key] = deque(maxlen=20)
        chat_media_history[chat_key].clear()
        last_random_reply.pop(chat_key, None)
        last_old_reply.pop(chat_key, None)
        toast = _t(lang, "cfg_memory_reset")

    await _edit_or_send(call, _config_text("tg", chat_id, user_id),
                        build_main_config_keyboard("tg", chat_id, user_id))
    await tg_bot.answer_callback_query(_cb_id(call), toast)

# ============================================================
# CALLBACK HANDLER (menu:)
# ============================================================
@_typed_decorator(tg_bot.callback_query_handler)(func=lambda call: bool(call.data and call.data.startswith("menu:")))
async def handle_menu_callback(call: telebot.types.CallbackQuery) -> None:
    msg = _tg_msg(call)
    data = call.data or ""
    action = data.split(":", 1)[1] if ":" in data else ""
    chat_id = msg.chat.id
    user_id = call.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    is_private = (msg.chat.type == 'private')

    if action == "close":
        try:
            await tg_bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass
        await _cleanup_config_children(chat_id, user_id)
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "settings":
        cfg_text = _config_text("tg", chat_id, user_id)
        kb = build_main_config_keyboard("tg", chat_id, user_id)
        try:
            await tg_bot.edit_message_text(
                cfg_text, chat_id, msg.message_id,
                parse_mode='HTML', reply_markup=kb,
            )
            config_msg_owners[msg.message_id] = user_id
        except Exception as e:
            logger.warning(f"menu:settings edit: {e}")
        await tg_bot.answer_callback_query(_cb_id(call))
        return

    if action == "help":
        await tg_bot.answer_callback_query(_cb_id(call))
        help_text = _t(lang, "help_body", MINI_APP_URL, GITHUB_URL)
        edited = await edit_rich_message(chat_id, msg.message_id, help_text)
        if not edited:
            try:
                await tg_bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
            await send_formatted(chat_id, help_text)
        return

    if action == "open":
        await tg_bot.answer_callback_query(_cb_id(call))
        menu_text = _build_menu_text(lang)
        kb = build_menu_keyboard(lang, is_private=is_private)
        edited = await edit_rich_message(chat_id, msg.message_id, menu_text, reply_markup=kb)
        if not edited:
            try:
                await tg_bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
            await send_formatted(chat_id, menu_text, reply_markup=kb)
        return

# ============================================================
# TELEGRAM: HELP / MENU / START / DONATE
# ============================================================
@_typed_decorator(tg_bot.message_handler)(commands=['start'])
async def handle_start(message: telebot.types.Message) -> None:
    args = telebot.util.extract_arguments(message.text or "")
    if args:
        if args.startswith('donate_stars_'):
            try:
                stars = int(args.split('_')[-1])
                if stars <= 0:
                    raise ValueError
            except (ValueError, IndexError):
                await reply_tg_html(message, "❌ Неверное количество звёзд.")
                return
            pending_donations[message.chat.id] = stars
            prices = [cast(Any, telebot.types.LabeledPrice)(label="💎 Поддержать Кульша", amount=stars)]
            await tg_bot.send_invoice(
                chat_id=message.chat.id, title="💎 Донат Кульшу",
                description=f"💖 Поддержка разработки на {stars} ⭐",
                invoice_payload=f"donate_{stars}_stars", provider_token="",
                currency="XTR", prices=prices, start_parameter="donate",
            )
            return

    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    is_private = (message.chat.type == 'private')

    start_text = _build_start_text(lang)
    kb = build_start_keyboard(lang, is_private=is_private)
    await send_formatted(chat_id, start_text, reply_to=message.message_id, reply_markup=kb)


@_typed_decorator(tg_bot.message_handler)(commands=['menu'])
async def handle_menu(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    is_private = (message.chat.type == 'private')

    menu_text = _build_menu_text(lang)
    kb = build_menu_keyboard(lang, is_private=is_private)
    await send_formatted(chat_id, menu_text, reply_to=message.message_id, reply_markup=kb)


@_typed_decorator(tg_bot.message_handler)(commands=['help'])
async def handle_help(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    cfg = get_user_config("tg", message.chat.id, message.from_user.id)
    lang = cfg.get("language", "ru")
    help_text = _t(lang, "help_body", MINI_APP_URL, GITHUB_URL)
    try:
        await send_formatted(message.chat.id, help_text, reply_to=message.message_id)
    except Exception:
        await tg_bot.send_message(
            message.chat.id, re.sub(r'<[^>]+>', '', help_text),
            reply_to_message_id=message.message_id,
        )


@_typed_decorator(tg_bot.message_handler)(commands=['donate'])
async def handle_donate(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    cfg = get_user_config("tg", message.chat.id, message.from_user.id)
    lang = cfg.get("language", "ru")
    text = (
        f"# {_t(lang, 'donate_title')}\n\n"
        f"✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"{_t(lang, 'donate_intro')}\n\n"
        f"**{_t(lang, 'donate_methods')}**\n"
        f"▸ {_t(lang, 'donate_online')}: {DONATE_URL}\n"
        f"▸ {_t(lang, 'donate_stars_hint')}\n\n"
        f"🔗 GitHub: {GITHUB_URL}"
    )
    try:
        await send_formatted(message.chat.id, text, reply_to=message.message_id)
    except Exception:
        await reply_tg_html(message, f"Поддержать Кульша: {DONATE_URL} 🍷🗿")


@_typed_decorator(tg_bot.message_handler)(commands=['donate_stars'])
async def handle_donate_stars(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    cfg = get_user_config("tg", chat_id, message.from_user.id)
    lang = cfg.get("language", "ru")
    args = (telebot.util.extract_arguments(message.text or "") or "").strip()
    if not args:
        await reply_tg_html(message, _t(lang, "donate_stars_need"))
        return
    try:
        stars = int(args.split()[0])
        if stars <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await reply_tg_html(message, _t(lang, "donate_stars_bad"))
        return
    pending_donations[chat_id] = stars
    prices = [cast(Any, telebot.types.LabeledPrice)(label="Поддержать Кульша", amount=stars)]
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
        await reply_tg_html(message, _t(lang, "donate_invoice_fail", str(e)))


@_typed_decorator(tg_bot.message_handler)(commands=['credits'])
async def handle_credits(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    cfg = get_user_config("tg", message.chat.id, message.from_user.id)
    lang = cfg.get("language", "ru")
    creds = get_user_credits("tg", message.from_user.id)
    await reply_tg_html(message, _t(lang, "credits_balance", creds, DAILY_CREDITS))


@_typed_decorator(tg_bot.message_handler)(commands=['togglepremiumfunctionsadmin'])
async def handle_toggle_premium(message: telebot.types.Message) -> None:
    global premium_functions_enabled
    if message.from_user is None or message.from_user.id != PREMIUM_ADMIN_ID:
        await reply_tg_html(message, "⛔ Нет доступа.")
        return
    premium_functions_enabled = not premium_functions_enabled
    state = "включены ✅" if premium_functions_enabled else "выключены ❌"
    await reply_tg_html(message, f"Расширенные функции: {state}")


@_typed_decorator(tg_bot.pre_checkout_query_handler)(func=lambda query: True)
async def handle_pre_checkout(pre_checkout: telebot.types.PreCheckoutQuery) -> None:
    await tg_bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@_typed_decorator(tg_bot.message_handler)(content_types=['successful_payment'])
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
    cfg = get_user_config("tg", message.chat.id, user_id)
    lang = cfg.get("language", "ru")
    await reply_tg_html(message, _t(lang, "donate_thanks", stars))

# ============================================================
# TG CONFIG / AVATAR / RECALL / SEARCH / CHART
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
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    raw = await get_avatar_description_tg(message, chat_id, user_id, lang=lang)
    if not raw:
        await reply_tg_html(message, _t(lang, "avatar_fail"))
        return
    segments = clean_extra_text(raw)
    if not segments:
        await reply_tg_html(message, _t(lang, "avatar_fail"))
        return
    for i, seg in enumerate(segments):
        if i == 0:
            await reply_tg_html(message, seg)
        else:
            await send_tg_html(message.chat.id, seg)


async def tg_handle_recall_media(message: telebot.types.Message, chat_id: int, user_id: int, parts: list[str]) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    n = 3
    for p in parts:
        if p.isdigit():
            n = min(int(p), 10)
            break
    raw = await get_recall_media_description_tg(message, chat_id, user_id, n, lang=lang)
    if not raw:
        await reply_tg_html(message, _t(lang, "recall_fail"))
        return
    segments = clean_extra_text(raw)
    if not segments:
        await reply_tg_html(message, _t(lang, "recall_fail"))
        return
    for i, seg in enumerate(segments):
        if i == 0:
            await reply_tg_html(message, seg)
        else:
            await send_tg_html(message.chat.id, seg)


async def tg_handle_search(message: telebot.types.Message, query: str, chat_id: int, user_id: int) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    if not query.strip():
        await reply_tg_html(message, _t(lang, "search_need_query"))
        return
    status = await tg_bot.send_message(chat_id, _t(lang, "search_starting", query))
    results = await web_search(query, max_results=6)
    try:
        await tg_bot.delete_message(chat_id, status.message_id)
    except Exception:
        pass
    if not results:
        await reply_tg_html(message, _t(lang, "search_nothing"))
        return
    context = _format_search_results(results)
    # Пусть ИИ сам сформулирует ответ на основе результатов
    prompt = (
        f"Пользователь искал в интернете: {query}\n\n"
        f"Найденные результаты:\n{context}\n\n"
        f"Сформулируй краткий ответ (3-6 предложений) на основе этих результатов. "
        f"Если результаты не по теме — скажи об этом. "
        f"Не выдумывай факты. Ответь в стиле Кульша. "
        f"Без маркеров !search, !chart, !separate."
    )
    answer = await ask_ai_async(prompt=prompt, chat_id=chat_id, user_id=user_id, platform="tg")
    header = f"🔎 <b>{html.escape(query)}</b>\n"
    full = header + "\n" + (answer or "")
    sources = []
    for i, r in enumerate(results[:4], 1):
        sources.append(f"{i}. [{html.escape(r.get('title', '')[:60])}]({r.get('url', '')})")
    if sources:
        full += "\n\n<b>" + _t(lang, "search_source") + ":</b>\n" + "\n".join(sources)
    await send_formatted(chat_id, full, reply_to=message.message_id)


async def tg_handle_chart_request(message: telebot.types.Message, description: str,
                                  chat_id: int, user_id: int,
                                  user_images: list[bytes] | None = None) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    if not description.strip():
        await reply_tg_html(message, _t(lang, "chart_usage"))
        return
    status = await tg_bot.send_message(chat_id, _t(lang, "chart_building"))
    # Просим AI сгенерировать JSON-спецификацию
    chart_prompt = (
        f"Сгенерируй JSON-спецификацию инфографики по описанию:\n\n{description}\n\n"
        f"Верни ТОЛЬКО JSON-объект без markdown и без текста вокруг. "
        f"Структура:\n"
        f'{{"theme": "dark_modern|light_minimal|ocean|retro", "title": "...", "subtitle": "...", '
        f'"blocks": [{{"type": "heading"|"text"|"divider"|"bar"|"line"|"pie"|"pie3d"|"table"|"image", ...}}]}}\n'
        f"Используй реальные числовые данные, красивые заголовки. "
        f"Для изображений с URL — {{'type':'image','url':'https://...'}}."
    )
    raw = await ask_ai_async(
        prompt=chart_prompt,
        system_instruction_override=(
            "You are a data-visualization JSON generator. Output ONLY valid JSON. No markdown, no prose."
        ),
        chat_id=chat_id, user_id=user_id, platform="tg",
    )
    spec = None
    try:
        spec = json.loads(clean_json_text(raw))
    except Exception:
        # попробуем вытащить JSON из текста
        m = re.search(r'\{[\s\S]*\}', raw or "")
        if m:
            try:
                spec = json.loads(m.group(0))
            except Exception:
                spec = None
    if not isinstance(spec, dict):
        try:
            await tg_bot.edit_message_text(_t(lang, "chart_error", "invalid JSON"), chat_id, status.message_id)
        except Exception:
            pass
        return
    try:
        img = await render_infographic(spec, user_images=user_images)
    except Exception as e:
        logger.error(f"chart render error: {e}")
        try:
            await tg_bot.edit_message_text(_t(lang, "chart_error", str(e)), chat_id, status.message_id)
        except Exception:
            pass
        return
    try:
        await tg_bot.delete_message(chat_id, status.message_id)
    except Exception:
        pass
    try:
        await tg_bot.send_photo(
            chat_id, InputFile(img, file_name="infographic.png"),
            caption=spec.get("title") or _t(lang, "chart_built"),
            reply_to_message_id=message.message_id,
        )
    except Exception as e:
        logger.error(f"chart send error: {e}")
        await reply_tg_html(message, _t(lang, "chart_error", str(e)))

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
# SEND TG AI RESPONSE — с обработкой !search и !chart
# ============================================================
async def send_tg_ai_response(message: telebot.types.Message, chat_id: int, user_id: int,
                              answer_raw: str, user_text: str | None = None,
                              user_images: list[bytes] | None = None) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    separate_enabled = cfg.get("separate_enabled", True)
    streaming = cfg.get("streaming_enabled", False) and premium_functions_enabled

    if streaming and separate_enabled:
        streaming = False

    # ----- !search -----
    if cfg.get("web_search_enabled", True):
        query, remaining = _extract_search_marker(answer_raw or "")
        if query:
            # AI хочет поискать. Делаем поиск, отдаём результаты обратно в AI.
            results = await web_search(query, max_results=6)
            if results:
                context = _format_search_results(results)
                orig = user_text or (message.text or message.caption or "")
                follow_prompt = (
                    f"Пользователь спросил: {orig}\n\n"
                    f"Ты выполнил поиск: {query}\n\n"
                    f"Результаты поиска:\n{context}\n\n"
                    f"Ответь на основе этих результатов. Без маркеров !search, !chart. "
                    f"Дай краткий точный ответ, ссылайся на факты, не выдумывай."
                )
                answer_raw = await ask_ai_async(
                    prompt=follow_prompt,
                    chat_id=chat_id, user_id=user_id, platform="tg",
                )
            else:
                answer_raw = _t(lang, "search_nothing")

    # ----- !chart -----
    if premium_functions_enabled:
        chart_spec, remaining = _extract_chart_marker(answer_raw or "")
        if chart_spec:
            try:
                img = await render_infographic(chart_spec, user_images=user_images)
                try:
                    await tg_bot.send_photo(
                        chat_id, InputFile(img, file_name="infographic.png"),
                        caption=chart_spec.get("title") or _t(lang, "chart_built"),
                        reply_to_message_id=message.message_id,
                    )
                except Exception as e:
                    logger.error(f"chart send: {e}")
                answer_raw = remaining
            except Exception as e:
                logger.error(f"chart render: {e}")
                answer_raw = remaining + "\n" + _t(lang, "chart_error", str(e))

    clean_segments, markers = process_ai_response(answer_raw, separate_enabled=separate_enabled)

    extra_segments: list[str] = []
    if "avatar" in markers:
        markers.remove("avatar")
        try:
            ar = await get_avatar_description_tg(message, chat_id, user_id, lang=lang)
            if ar:
                extra_segments.extend(clean_extra_text(ar))
        except Exception as e:
            logger.warning(f"avatar desc failed: {e}")
    if "recall_media" in markers:
        markers.remove("recall_media")
        try:
            rr = await get_recall_media_description_tg(message, chat_id, user_id, 3, lang=lang)
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
            chat_id=chat_id, user_id=user_id, platform="tg",
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
# TOOLS
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
    def _do() -> list[str]:
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
    def _do() -> None:
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
    if message.from_user is None:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    status = await tg_bot.send_message(chat_id, _t(lang, "tool_unpacking"))
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
        await tg_bot.edit_message_text(_t(lang, "tool_unpacked", files_display),
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

        await tg_bot.edit_message_text(_t(lang, "tool_analyzing", len(contents)),
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
            await tg_bot.edit_message_text(_t(lang, "tool_parse_fail", str(e)),
                                           chat_id, status.message_id)
            return

        summary = data.get("summary", "готово")
        new_files = data.get("files", {})
        if not isinstance(new_files, dict) or not new_files:
            await tg_bot.edit_message_text(_t(lang, "tool_no_changes", summary),
                                           chat_id, status.message_id)
            return

        await tg_bot.edit_message_text(_t(lang, "tool_editing", len(new_files)),
                                       chat_id, status.message_id)
        for rel, new_content in new_files.items():
            full = _safe_join(work_dir, rel)
            if full is None:
                continue
            os.makedirs(os.path.dirname(full) or work_dir, exist_ok=True)
            with open(full, 'w', encoding='utf-8') as f:
                f.write(new_content)

        await tg_bot.edit_message_text(_t(lang, "tool_repacking"),
                                       chat_id, status.message_id)
        out_zip = os.path.join(work_dir, f"edited_{filename or 'archive.zip'}")
        await create_archive(work_dir, out_zip)

        await tg_bot.edit_message_text(_t(lang, "tool_sending"),
                                       chat_id, status.message_id)
        with open(out_zip, 'rb') as f:
            await tg_bot.send_document(
                chat_id, InputFile(f, file_name=os.path.basename(out_zip)),
                caption=f"🍷🗿 {summary}",
            )
        await tg_bot.edit_message_text(_t(lang, "tool_done"), chat_id, status.message_id)
    except Exception as e:
        logger.error(f"tool_edit_archive: {e}")
        try:
            await tg_bot.edit_message_text(_t(lang, "tool_error", str(e)), chat_id, status.message_id)
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
    if message.from_user is None:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    try:
        text = file_bytes.decode('utf-8', errors='replace')
    except Exception:
        await reply_tg_html(message, "не могу прочитать файл как текст")
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
@_typed_decorator(tg_bot.message_handler)(content_types=['photo', 'video', 'animation', 'document', 'sticker'])
async def handle_tg_media(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
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
        media_tag = "[фото]" if lang == "ru" else "[photo]"
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
        media_tag = "[видео]" if lang == "ru" else "[video]"
    elif message.animation:
        file_id = message.animation.file_id
        media_type = "animation"
        media_tag = "[гифка]" if lang == "ru" else "[gif]"
    elif message.document:
        file_id = message.document.file_id
        media_type = "document"
        file_name = message.document.file_name or "file"
        media_tag = f"[док: {file_name}]" if lang == "ru" else f"[doc: {file_name}]"
    elif message.sticker:
        file_id = message.sticker.file_id
        media_type = "sticker"
        media_tag = "[стикер]" if lang == "ru" else "[sticker]"

    if file_id and media_tag:
        add_media_history(chat_key, None, media_type or "media", display_name, file_id=file_id, caption=caption)

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
            await reply_tg_html(message, _t(lang, "battle_need_photos"))
        return

    if message.media_group_id and message.media_group_id in battle_photos and message.photo:
        img_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
        battle_photos[message.media_group_id].append(img_bytes)
        return

    # chart по описанию + фото пользователя
    if is_dm or re.search(r'(?i)\bкульш\s+(график|chart|инфографика)', caption or ""):
        m = re.match(r'(?i)кульш\s+(график|chart|инфографика)\s*(.*)', caption or "", re.DOTALL)
        if m and message.photo:
            try:
                img_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
                await tg_handle_chart_request(message, m.group(2).strip() or "инфографика с этим фото",
                                              chat_id, user_id, user_images=[img_bytes])
            except Exception as e:
                logger.error(f"chart with user image err: {e}")
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
        status = await tg_bot.send_message(chat_id, _t(lang, "psl_analyzing"))
        try:
            img_bytes = await get_tg_file_bytes(tg_bot, message.photo[-1].file_id)
            reply_text = message.reply_to_message.text if message.reply_to_message else None
            include_advice = bool(
                "совет" in cl or "advice" in cl or
                (reply_text and ("совет" in reply_text.lower() or "advice" in reply_text.lower()))
            )
            theme = cfg.get("theme", "dark")
            ai_data = await get_looksmaxxing_data(img_bytes, include_advice, lang=lang)
            if "error" in ai_data:
                await tg_bot.edit_message_text(ai_data['error'], chat_id, status.message_id)
                return
            infographic = await create_infographic(img_bytes, ai_data, theme=theme, lang=lang)
            report_text = (
                f"<b>{_t(lang, 'psl_title')}</b>\n\n"
                f"{_t(lang, 'psl_gender')} {ai_data.get('gender', '?')}\n"
                f"{_t(lang, 'psl_score')} <code>{ai_data.get('psl', '?')}/8.0</code>\n"
                f"{_t(lang, 'psl_tier')} <code>{ai_data.get('tier', '?')}</code>\n"
            )
            if ai_data.get("potential"):
                report_text += f"{_t(lang, 'psl_potential')} <code>{ai_data['potential']}</code>\n"
            report_text += f"\n<b>{_t(lang, 'psl_analysis')}</b>\n{html.escape(ai_data.get('summary', ''))}"
            if include_advice and ai_data.get("advice"):
                report_text += f"\n\n<b>{_t(lang, 'psl_advice')}</b>\n{html.escape(ai_data['advice'])}"
            try:
                await tg_bot.send_photo(chat_id, InputFile(infographic),
                                        caption=_t(lang, "psl_report"))
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
            await reply_tg_html(message, f"🌋 Ошибка: {e}")
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
                    _t(lang, "tool_no_credits", COST_ARCHIVE_EDIT, credits, DAILY_CREDITS),
                )
                return
            spend_credits("tg", user_id, COST_ARCHIVE_EDIT)
            try:
                file_bytes = await get_tg_file_bytes(tg_bot, message.document.file_id)
            except Exception as e:
                await reply_tg_html(message, _t(lang, "tool_download_fail", str(e)))
                return
            default_req = "отредактируй что-нибудь полезное" if lang == "ru" else "edit something useful"
            await tool_edit_archive(message, caption.strip() or default_req,
                                    file_bytes, doc_name or "archive.zip")
            return

        if ext in TEXT_EXTS or mime.startswith("text/"):
            try:
                file_bytes = await get_tg_file_bytes(tg_bot, message.document.file_id)
            except Exception as e:
                await reply_tg_html(message, _t(lang, "tool_download_fail", str(e)))
                return
            default_req = _t(lang, "tool_review_empty")
            await tool_review_file(message, caption.strip() or default_req, file_bytes, doc_name or "file")
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
            if answer and answer.strip() and answer.strip().upper() not in ("НЕТ", "NO"):
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

    default_prompt = "че на этом?" if lang == "ru" else "what's this?"
    prompt = caption.strip() or default_prompt
    add_user_memory(chat_key, "TG", display_name, username, user_id,
                    f"{prompt} [с медиа: {media_tag}]", [media_tag or "медиа"],
                    message_id=message.message_id)
    messages = memory_to_messages(get_chat_memory(chat_key))
    answer = await ask_ai_async(messages=messages, image_bytes=image_bytes,
                                image_mime=image_mime, chat_id=chat_id,
                                user_id=user_id, platform="tg")
    user_imgs = [image_bytes] if image_bytes else None
    await send_tg_ai_response(message, chat_id, user_id, answer, user_text=prompt, user_images=user_imgs)
    asyncio.create_task(extract_memory(chat_key, f"{display_name}: [медиа] {caption}", answer))

# ============================================================
# TG TEXT HANDLER
# ============================================================
@_typed_decorator(tg_bot.message_handler)(func=lambda m: m.text is not None, content_types=['text'])
async def handle_tg_text(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_dm = message.chat.type == 'private'
    text = message.text or ""
    tl = text.lower()
    display_name = message.from_user.full_name or "Unknown"
    username = message.from_user.username or ""
    chat_key = f"tg_{chat_id}"

    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")

    if user_id in prompt_waiting:
        waiting_msg_id = prompt_waiting.pop(user_id, None)
        new_prompt = text.strip()
        if new_prompt.lower() in ("отмена", "cancel", "/cancel", "отменить"):
            cfg["custom_prompt"] = None
            if waiting_msg_id:
                try:
                    await tg_bot.edit_message_text(
                        _t(lang, "prompt_cancelled"),
                        chat_id, waiting_msg_id,
                    )
                except Exception:
                    pass
        else:
            truncated = new_prompt[:2000]
            cfg["custom_prompt"] = truncated
            if waiting_msg_id:
                try:
                    await tg_bot.edit_message_text(
                        _t(lang, "prompt_saved", len(truncated)),
                        chat_id, waiting_msg_id,
                    )
                except Exception:
                    pass
        return

    if tl.startswith("кульш конфиг") or tl.startswith("кульш настройки") or tl.startswith("kulsh config"):
        await tg_handle_config(message)
        return

    # ---- поиск ----
    m = re.match(r'(?i)^(?:кульш\s+)?(?:поиск|search|найди|найти)\s+(.+)$', text.strip(), re.DOTALL)
    if m:
        await tg_handle_search(message, m.group(1).strip(), chat_id, user_id)
        return

    # ---- график ----
    m = re.match(r'(?i)^(?:кульш\s+)?(?:график|chart|инфографика|диаграмма)\s+(.+)$', text.strip(), re.DOTALL)
    if m:
        await tg_handle_chart_request(message, m.group(1).strip(), chat_id, user_id)
        return

    if tl.startswith("кульш донаты") or tl.startswith("kulsh donations"):
        top = get_top_donators()
        if not top:
            await reply_tg_html(message, _t(lang, "top_donators_empty", DONATE_URL))
            return
        lines = [f"{_t(lang, 'top_donators_title')}\n"]
        for i, (name, total) in enumerate(top, 1):
            lines.append(_t(lang, "top_donators_item", i, html.escape(name), total))
        await send_formatted(chat_id, "\n".join(lines), reply_to=message.message_id)
        return

    if tl.startswith("кульш аватарк") or tl.startswith("кульш аватар") or tl.startswith("kulsh avatar") or tl.strip() in ("!avatar", "! avatar"):
        await tg_handle_avatar(message, chat_id, user_id)
        return

    if tl.startswith("кульш вспомни медиа") or tl.startswith("kulsh recall") or "!recall_media" in tl:
        await tg_handle_recall_media(message, chat_id, user_id, text.split())
        return

    if tl.startswith("кульш логи") or tl.startswith("kulsh logs"):
        if user_id != PREMIUM_ADMIN_ID:
            try:
                member = await tg_bot.get_chat_member(chat_id, user_id)
                if member.status not in ('administrator', 'creator'):
                    await reply_tg_html(message, _t(lang, "logs_no_access"))
                    return
            except Exception:
                await reply_tg_html(message, _t(lang, "logs_cant_check"))
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
            await reply_tg_html(message, _t(lang, "logs_read_error", str(e)))
        return

    if is_looksmaxxing_command(text):
        user_looksmaxxing_state[chat_id] = True
        add_user_memory(chat_key, "TG", display_name, username, user_id, text, message_id=message.message_id)
        await reply_tg_html(message, _t(lang, "psl_need_photo"))
        return

    if is_battle_command(text):
        add_user_memory(chat_key, "TG", display_name, username, user_id, text, message_id=message.message_id)
        await reply_tg_html(message, _t(lang, "battle_need_photos"))
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
        await send_tg_ai_response(message, chat_id, user_id, answer, user_text=text)
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
            if answer and answer.strip() and answer.strip().upper() not in ("НЕТ", "NO"):
                last_random_reply[chat_key] = time.time()
                await send_tg_ai_response(message, chat_id, user_id, answer)
        except Exception as e:
            logger.warning(f"Random reply: {e}")

# ============================================================
# BATTLE MEDIA GROUP
# ============================================================
async def process_battle_media_group(media_group_id: str, tg_chat_id: int, user_id: int) -> None:
    for _ in range(10):
        if media_group_id in battle_photos and len(battle_photos[media_group_id]) >= 2:
            break
        await asyncio.sleep(0.5)
    cfg = get_user_config("tg", tg_chat_id, user_id)
    lang = cfg.get("language", "ru")
    if media_group_id not in battle_photos or len(battle_photos[media_group_id]) < 2:
        battle_photos.pop(media_group_id, None)
        battle_media_groups.pop(media_group_id, None)
        await tg_bot.send_message(tg_chat_id, _t(lang, "battle_need_photos"))
        return
    photos = battle_photos.pop(media_group_id)
    battle_media_groups.pop(media_group_id, None)
    photo1_bytes, photo2_bytes = photos[:2]
    theme = cfg.get("theme", "dark")
    try:
        await tg_bot.send_chat_action(tg_chat_id, 'typing')
    except Exception:
        pass
    status = await tg_bot.send_message(tg_chat_id, _t(lang, "battle_waiting"))
    ai_data = await get_battle_data(photo1_bytes, photo2_bytes, lang=lang)
    if "error" in ai_data:
        await tg_bot.edit_message_text(ai_data['error'], tg_chat_id, status.message_id)
        return
    battle_img = await create_battle_infographic(photo1_bytes, photo2_bytes, ai_data,
                                                  theme=theme, lang=lang)
    winner_num = str(ai_data.get("winner", "1"))
    winner_label = _t(lang, "battle_first") if winner_num == "1" else _t(lang, "battle_second")
    report_text = (
        f"<b>{_t(lang, 'battle_title')}</b>\n\n"
        f"{_t(lang, 'battle_winner')} <b>{winner_label}</b>\n"
        f"{_t(lang, 'battle_reason')} {html.escape(ai_data.get('reason', ''))}\n\n"
        f"{_t(lang, 'battle_photo1')} PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
        f"Tier {html.escape(ai_data.get('photo1', {}).get('tier', '?'))}\n"
        f"{_t(lang, 'battle_photo2')} PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
        f"Tier {html.escape(ai_data.get('photo2', {}).get('tier', '?'))}\n"
    )
    try:
        await tg_bot.send_photo(tg_chat_id, InputFile(battle_img), caption=_t(lang, "battle_caption"))
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
# DISCORD: SEND AI RESPONSE (с обработкой !search и !chart)
# ============================================================
async def send_ds_ai_response(message: discord.Message, chat_id: int, user_id: int,
                              answer_raw: str, user_text: str | None = None) -> None:
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    separate_enabled = cfg.get("separate_enabled", True)

    # !search
    if cfg.get("web_search_enabled", True):
        query, _ = _extract_search_marker(answer_raw or "")
        if query:
            results = await web_search(query, max_results=6)
            if results:
                context = _format_search_results(results)
                orig = user_text or message.content
                follow_prompt = (
                    f"Пользователь спросил: {orig}\n\n"
                    f"Ты выполнил поиск: {query}\n\n"
                    f"Результаты поиска:\n{context}\n\n"
                    f"Ответь на основе этих результатов. Без маркеров !search, !chart. "
                    f"Дай краткий точный ответ."
                )
                answer_raw = await ask_ai_async(
                    prompt=follow_prompt,
                    chat_id=chat_id, user_id=user_id, platform="ds",
                )
            else:
                answer_raw = _t(lang, "search_nothing")

    # !chart
    if premium_functions_enabled:
        chart_spec, remaining = _extract_chart_marker(answer_raw or "")
        if chart_spec:
            try:
                img = await render_infographic(chart_spec, user_images=None)
                try:
                    await message.reply(file=discord.File(fp=img, filename="infographic.png"),
                                        content=(chart_spec.get("title") or _t(lang, "chart_built"))[:1900])
                except Exception as e:
                    logger.error(f"ds chart send: {e}")
                answer_raw = remaining
            except Exception as e:
                logger.error(f"ds chart render: {e}")
                answer_raw = remaining + "\n" + _t(lang, "chart_error", str(e))

    clean_segments, markers = process_ai_response(answer_raw, separate_enabled=separate_enabled)

    extra_segments: list[str] = []
    if "avatar" in markers:
        markers.remove("avatar")
        try:
            ar = await get_avatar_description_ds(message, chat_id, user_id, lang=lang)
            if ar:
                extra_segments.extend(clean_extra_text(ar))
        except Exception as e:
            logger.warning(f"DS avatar: {e}")
    if "recall_media" in markers:
        markers.remove("recall_media")
        history = list(chat_media_history.get(f"ds_{chat_id}", []))
        if history:
            last = history[-3:]
            lines = [f"- {it.get('type', 'media')} {it.get('sender', '?')}: {(it.get('caption') or '')[:100]}"
                     for it in last]
            extra_segments.append("📎 " + "\n".join(lines))

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
# DISCORD CONFIG
# ============================================================
def _ds_config_embed(chat_id: int, user_id: int) -> discord.Embed:
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    series = _t(lang, "on") if cfg.get("series_reminder_enabled", True) else _t(lang, "off")
    stickers = _t(lang, "on") if cfg.get("stickers_enabled", True) else _t(lang, "off")
    sep = _t(lang, "on") if cfg.get("separate_enabled", True) else _t(lang, "off")
    autoreply = _t(lang, "on") if cfg.get("random_reply_enabled", False) else _t(lang, "off")
    random_msgs = _t(lang, "on") if cfg.get("random_messages_enabled", True) else _t(lang, "off")
    websearch = _t(lang, "on") if cfg.get("web_search_enabled", True) else _t(lang, "off")
    prompt = cfg.get("custom_prompt") or ("стандартный" if lang == "ru" else "default")
    if len(prompt) > 900:
        prompt = prompt[:900] + "..."
    theme_disp = _t(lang, "dark") if cfg.get("theme", "dark") == "dark" else _t(lang, "light")
    lang_disp = _t(lang, "russian") if lang == "ru" else _t(lang, "english")

    title = "✦ Настройки Кульша ✦" if lang == "ru" else "✦ Kulsh Settings ✦"
    desc = ("Текущие параметры канала. Изменение — текстом через `кульш конфиг <параметр> <значение>`."
            if lang == "ru" else
            "Current channel parameters. Change via text `kulsh config <param> <value>`.")

    embed = discord.Embed(title=title, color=0x10B981, description=desc)
    if lang == "ru":
        embed.add_field(name="🌐 Язык", value=lang_disp, inline=True)
        embed.add_field(name="🌓 Тема", value=theme_disp, inline=True)
        embed.add_field(name="🧠 Модель", value=model_display_name(cfg.get("model"), lang), inline=True)
        embed.add_field(name="🎛 Температура", value=str(cfg.get("temperature", 0.9)), inline=True)
        embed.add_field(name="💬 Разбивка", value=sep, inline=True)
        embed.add_field(name="🎨 Стикеры/гифки", value=stickers, inline=True)
        embed.add_field(name="🗣 Автоответ", value=autoreply, inline=True)
        embed.add_field(name="📢 Случайные сообщения", value=random_msgs, inline=True)
        embed.add_field(name="🔎 Веб-поиск", value=websearch, inline=True)
        embed.add_field(name="🎬 Серия", value=series, inline=True)
        embed.add_field(name="📝 Кастомный промпт", value=prompt, inline=False)
        embed.add_field(
            name="📖 Команды настройки",
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
                "`кульш конфиг поиск вкл|выкл`\n"
                "`кульш конфиг промпт <текст|сброс>`\n"
                "`кульш конфиг серия вкл|выкл`"
            ),
            inline=False,
        )
    else:
        embed.add_field(name="🌐 Language", value=lang_disp, inline=True)
        embed.add_field(name="🌓 Theme", value=theme_disp, inline=True)
        embed.add_field(name="🧠 Model", value=model_display_name(cfg.get("model"), lang), inline=True)
        embed.add_field(name="🎛 Temperature", value=str(cfg.get("temperature", 0.9)), inline=True)
        embed.add_field(name="💬 Split", value=sep, inline=True)
        embed.add_field(name="🎨 Stickers/GIFs", value=stickers, inline=True)
        embed.add_field(name="🗣 Auto-reply", value=autoreply, inline=True)
        embed.add_field(name="📢 Random messages", value=random_msgs, inline=True)
        embed.add_field(name="🔎 Web search", value=websearch, inline=True)
        embed.add_field(name="🎬 Series reminder", value=series, inline=True)
        embed.add_field(name="📝 Custom prompt", value=prompt, inline=False)
        embed.add_field(
            name="📖 Config commands",
            value=(
                "`kulsh config language ru|en`\n"
                "`kulsh config theme dark|light`\n"
                "`kulsh config model` — list\n"
                "`kulsh config model <number|auto>`\n"
                "`kulsh config temperature <0.0-2.0>`\n"
                "`kulsh config split on|off`\n"
                "`kulsh config stickers on|off`\n"
                "`kulsh config autoreply on|off`\n"
                "`kulsh config random on|off`\n"
                "`kulsh config search on|off`\n"
                "`kulsh config prompt <text|reset>`\n"
                "`kulsh config series on|off`"
            ),
            inline=False,
        )
    return embed


async def ds_handle_config(message: discord.Message, user_id: int) -> None:
    chat_id = message.channel.id
    member = _as_member(message.author)
    if message.guild and not (member and member.guild_permissions.administrator):
        cfg = get_user_config("ds", chat_id, user_id)
        lang = cfg.get("language", "ru")
        await message.reply(_t(lang, "ds_only_admins"))
        return
    embed = _ds_config_embed(chat_id, user_id)
    await message.reply(embed=embed)


async def ds_handle_config_param(message: discord.Message, user_id: int, parts: list[str]) -> None:
    chat_id = message.channel.id
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    member = _as_member(message.author)
    if message.guild and not (member and member.guild_permissions.administrator):
        await message.reply(_t(lang, "ds_only_admins"))
        return
    if len(parts) < 3:
        await ds_handle_config(message, user_id)
        return
    param = parts[2].lower()
    val = parts[3].lower() if len(parts) >= 4 else ""
    bool_on = val in ("вкл", "on", "1", "true", "да", "yes")

    if param in ("язык", "language"):
        if val in ("ru", "русский", "russian"):
            cfg["language"] = "ru"
            await message.reply(_t("ru", "ds_setting_lang", _t("ru", "russian")))
        elif val in ("en", "английский", "english"):
            cfg["language"] = "en"
            await message.reply(_t("en", "ds_setting_lang", _t("en", "english")))
        else:
            await message.reply(_t(lang, "ds_need_specify_ru_en"))
    elif param in ("тема", "theme"):
        if val in ("тёмная", "темная", "dark"):
            cfg["theme"] = "dark"
            await message.reply(_t(lang, "ds_setting_theme", _t(lang, "dark")))
        elif val in ("светлая", "light"):
            cfg["theme"] = "light"
            await message.reply(_t(lang, "ds_setting_theme", _t(lang, "light")))
        else:
            await message.reply(_t(lang, "ds_need_specify_theme"))
    elif param in ("серия", "series"):
        cfg["series_reminder_enabled"] = bool_on
        await message.reply(_t(lang, "ds_setting_series", _t(lang, "on") if bool_on else _t(lang, "off")))
    elif param in ("стикеры", "stickers"):
        cfg["stickers_enabled"] = bool_on
        await message.reply(_t(lang, "ds_setting_stickers", _t(lang, "on") if bool_on else _t(lang, "off")))
    elif param in ("разбивка", "split"):
        cfg["separate_enabled"] = bool_on
        await message.reply(_t(lang, "ds_setting_sep", _t(lang, "on") if bool_on else _t(lang, "off")))
    elif param in ("автоответ", "autoreply"):
        cfg["random_reply_enabled"] = bool_on
        await message.reply(_t(lang, "ds_setting_autoreply", _t(lang, "on") if bool_on else _t(lang, "off")))
    elif param in ("рандом", "random"):
        cfg["random_messages_enabled"] = bool_on
        await message.reply(_t(lang, "ds_setting_random", _t(lang, "on") if bool_on else _t(lang, "off")))
    elif param in ("поиск", "search"):
        cfg["web_search_enabled"] = bool_on
        await message.reply(_t(lang, "ds_setting_websearch", _t(lang, "on") if bool_on else _t(lang, "off")))
    elif param in ("температура", "temperature"):
        try:
            t = max(0.0, min(2.0, float(val)))
            cfg["temperature"] = t
            await message.reply(_t(lang, "ds_setting_temp", t))
        except ValueError:
            await message.reply(_t(lang, "ds_setting_temp_bad"))
    elif param in ("промпт", "prompt"):
        new_prompt = " ".join(parts[3:]).strip()
        if new_prompt.lower() in ("сброс", "reset", "убрать", "стандарт", "default"):
            cfg["custom_prompt"] = None
            await message.reply(_t(lang, "ds_setting_prompt_reset"))
        elif new_prompt:
            cfg["custom_prompt"] = new_prompt[:2000]
            await message.reply(_t(lang, "ds_setting_prompt_set"))
        else:
            await message.reply(_t(lang, "ds_setting_prompt_need"))
    elif param in ("модель", "model"):
        if not val:
            lines = [f"`{i}` — {MODEL_DISPLAY.get(m, m)}" for i, m in enumerate(MODEL_LIST)]
            await message.reply(
                f"{_t(lang, 'ds_setting_model', model_display_name(cfg.get('model'), lang))}\n\n" + "\n".join(lines)
            )
        elif val in ("авто", "auto"):
            cfg["model"] = None
            await message.reply(_t(lang, "ds_setting_model_auto"))
        else:
            try:
                idx = int(val)
                if 0 <= idx < len(MODEL_LIST):
                    cfg["model"] = MODEL_LIST[idx]
                    await message.reply(_t(lang, "ds_setting_model",
                                            MODEL_DISPLAY.get(MODEL_LIST[idx], MODEL_LIST[idx])))
                else:
                    await message.reply(_t(lang, "ds_setting_model_badnum"))
            except ValueError:
                await message.reply(_t(lang, "ds_setting_model_bad"))
    else:
        await message.reply(_t(lang, "ds_unknown_param"))

# ============================================================
# DISCORD SLASH
# ============================================================
def _ds_slash_help(lang: str) -> str:
    return _t(lang, "help_body", MINI_APP_URL, GITHUB_URL)


def _ds_slash_menu(lang: str) -> str:
    if lang == "ru":
        return (
            "# ✦ Кульш AI — меню ✦\n\n"
            "✦彡巛〢 ✦ 彡 巛 〢 ✦\n\n"
            "Открытая языковая модель с набором встроенных инструментов.\n\n"
            "**Основные**\n"
            "▸ `/start` — приветствие\n"
            "▸ `/help` — полный список команд\n"
            "▸ `/config` — настройки канала\n"
            "▸ `/donate` — поддержка разработки\n"
            "▸ `/credits` — баланс кредитов\n\n"
            "**Инструменты**\n"
            "▸ `/avatar` — описать аватарку\n"
            "▸ `/recall` — вспомнить последние медиа\n"
            "▸ `/psl` — оценка внешности\n"
            "▸ `/battle` — баттл двух фото\n"
            "▸ `/logs` — логи сервера (админам)\n\n"
            f"🍷🗿 {MINI_APP_URL}"
        )
    return (
        "# ✦ Kulsh AI — menu ✦\n\n"
        "✦彡巛〢 ✦ 彡 巛 〢 ✦\n\n"
        "An open-source language model with built-in tools.\n\n"
        "**Basics**\n"
        "▸ `/start` — greeting\n"
        "▸ `/help` — command list\n"
        "▸ `/config` — channel settings\n"
        "▸ `/donate` — support development\n"
        "▸ `/credits` — credits balance\n\n"
        "**Tools**\n"
        "▸ `/avatar` — describe avatar\n"
        "▸ `/recall` — recall recent media\n"
        "▸ `/psl` — looksmaxxing\n"
        "▸ `/battle` — two-photo battle\n"
        "▸ `/logs` — server logs (admins)\n\n"
        f"🍷🗿 {MINI_APP_URL}"
    )


def _ds_slash_start(lang: str) -> str:
    if lang == "ru":
        return (
            "# 🍷🗿 Кульш на связи\n\n"
            "✦彡巛〢 ✦ 彡 巛 〢 ✦\n\n"
            "Открытая языковая модель с анализом изображений и настройкой под себя.\n\n"
            "**🚀 С чего начать**\n"
            "▸ `/menu` — все разделы\n"
            "▸ `/help` — список команд\n"
            "▸ `/config` — настройки канала\n\n"
            f"🍷🗿 {MINI_APP_URL}"
        )
    return (
        "# 🍷🗿 Kulsh is online\n\n"
        "✦彡巛〢 ✦ 彡 巛 〢 ✦\n\n"
        "An open-source language model with image analysis and personal configuration.\n\n"
        "**🚀 Get started**\n"
        "▸ `/menu` — all sections\n"
        "▸ `/help` — command list\n"
        "▸ `/config` — channel settings\n\n"
        f"🍷🗿 {MINI_APP_URL}"
    )


def _ds_lang_of(interaction: discord.Interaction) -> str:
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    return lang if isinstance(lang, str) else "ru"


@ds_tree.command(name="start", description="Greeting / Приветствие")
async def ds_slash_start(interaction: discord.Interaction) -> None:
    lang = _ds_lang_of(interaction)
    await interaction.response.send_message(_ds_slash_start(lang))


@ds_tree.command(name="menu", description="Menu / Меню")
async def ds_slash_menu(interaction: discord.Interaction) -> None:
    lang = _ds_lang_of(interaction)
    await interaction.response.send_message(_ds_slash_menu(lang))


@ds_tree.command(name="help", description="Command list / Список команд")
async def ds_slash_help(interaction: discord.Interaction) -> None:
    lang = _ds_lang_of(interaction)
    await interaction.response.send_message(_ds_slash_help(lang))


@ds_tree.command(name="donate", description="Support the project / Поддержать проект")
async def ds_slash_donate(interaction: discord.Interaction) -> None:
    lang = _ds_lang_of(interaction)
    text = (
        f"# {_t(lang, 'donate_title')}\n\n"
        f"✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"{_t(lang, 'donate_intro')}\n\n"
        f"▸ {_t(lang, 'donate_online')}: {DONATE_URL}\n"
        f"🔗 GitHub: {GITHUB_URL}"
    )
    await interaction.response.send_message(text)


@ds_tree.command(name="credits", description="Credits balance / Баланс кредитов")
async def ds_slash_credits(interaction: discord.Interaction) -> None:
    lang = _ds_lang_of(interaction)
    creds = get_user_credits("ds", interaction.user.id)
    await interaction.response.send_message(_t(lang, "credits_balance", creds, DAILY_CREDITS))


@ds_tree.command(name="config", description="Channel settings / Настройки канала")
async def ds_slash_config(interaction: discord.Interaction) -> None:
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    member = _as_member(interaction.user)
    if interaction.guild and not (member and member.guild_permissions.administrator):
        await interaction.response.send_message(_t(lang, "ds_only_admins"), ephemeral=True)
        return
    embed = _ds_config_embed(chat_id, user_id)
    await interaction.response.send_message(embed=embed)


@ds_tree.command(name="avatar", description="Describe avatar / Описать аватарку")
@app_commands.describe(user="Whose avatar to describe / Чью аватарку описать")
async def ds_slash_avatar(interaction: discord.Interaction, user: discord.Member | None = None) -> None:
    await interaction.response.defer()
    target = user or interaction.user
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    try:
        img_bytes = await download_image_bytes(target.display_avatar.url)
        prompt = (
            f"Ты только что посмотрел аватарку пользователя {target.display_name}. "
            f"Опиши коротко (1-2 предложения) в стиле Кульша. Без markdown. "
            f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
            if lang == "ru" else
            f"You've just seen the avatar of {target.display_name}. "
            f"Describe briefly (1-2 sentences) in Kulsh's style. No markdown. "
            f"Do NOT use markers !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
        )
        raw = await ask_ai_async(
            prompt=prompt, image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id, platform="ds",
        )
        segments = clean_extra_text(raw) if raw else []
        if not segments:
            await interaction.followup.send(_t(lang, "avatar_fail"))
            return
        for seg in segments:
            await interaction.followup.send(seg)
    except Exception as e:
        logger.error(f"DS slash avatar: {e}")
        await interaction.followup.send(f"Ошибка: {e}")


@ds_tree.command(name="recall", description="Recall recent media / Вспомнить недавние медиа")
@app_commands.describe(count="How many last items / Сколько последних элементов")
async def ds_slash_recall(interaction: discord.Interaction, count: int = 3) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    n = max(1, min(10, count))
    history = list(chat_media_history.get(f"ds_{chat_id}", []))
    if not history:
        await interaction.followup.send(_t(lang, "recall_fail"))
        return
    last = history[-n:]
    lines = [f"- {it.get('type', 'media')} {it.get('sender', '?')}: {(it.get('caption') or '')[:120]}"
             for it in last]
    meta = "\n".join(lines)
    try:
        prompt = (
            f"Ты вспоминаешь недавние медиа. Список:\n{meta}\n\n"
            f"Коротко прокомментируй в стиле Кульша. Без markdown. "
            f"НЕ используй маркеры !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
            if lang == "ru" else
            f"You recall recent media. List:\n{meta}\n\n"
            f"Comment briefly in Kulsh's style. No markdown. "
            f"Do NOT use markers !separate, !avatar, !recall_media, !sticker, !gif, !search, !chart."
        )
        raw = await ask_ai_async(
            prompt=prompt, chat_id=chat_id, user_id=user_id, platform="ds",
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
async def ds_slash_logs(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    lang = _ds_lang_of(interaction)
    if interaction.user.id not in AUTHORIZED_UPDATERS:
        await interaction.followup.send(_t(lang, "ds_update_no_access"), ephemeral=True)
        return
    try:
        tail = read_log_tail(20)
        intro = _t(lang, "ds_logs_content")
        content = f"{intro}\n```\n{tail}\n```" if len(tail) <= 1900 else f"{intro}\n\n{tail[:1900]}"
        try:
            await interaction.followup.send(content=content, file=discord.File('bot.log'), ephemeral=True)
        except FileNotFoundError:
            await interaction.followup.send(content=content, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}", ephemeral=True)


@ds_tree.command(name="search", description="Web search / Поиск в интернете")
@app_commands.describe(query="What to search / Что искать")
async def ds_slash_search(interaction: discord.Interaction, query: str) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    cfg = get_user_config("ds", chat_id, user_id)
    if not cfg.get("web_search_enabled", True):
        await interaction.followup.send(_t(lang, "search_off"))
        return
    results = await web_search(query, max_results=6)
    if not results:
        await interaction.followup.send(_t(lang, "search_nothing"))
        return
    context = _format_search_results(results)
    prompt = (
        f"Пользователь искал в интернете: {query}\n\n"
        f"Найденные результаты:\n{context}\n\n"
        f"Сформулируй краткий ответ (3-6 предложений) на основе этих результатов. "
        f"Ответь в стиле Кульша. Без маркеров !search, !chart."
    )
    answer = await ask_ai_async(prompt=prompt, chat_id=chat_id, user_id=user_id, platform="ds")
    full = f"🔎 **{query}**\n\n{answer or ''}"
    sources = [f"{i}. [{r.get('title', '')[:60]}]({r.get('url', '')})" for i, r in enumerate(results[:4], 1)]
    if sources:
        full += "\n\n**" + _t(lang, "search_source") + ":**\n" + "\n".join(sources)
    await interaction.followup.send(full[:1900])


@ds_tree.command(name="chart", description="Generate infographic / Сгенерировать инфографику")
@app_commands.describe(description="Describe the chart / Опиши график")
async def ds_slash_chart(interaction: discord.Interaction, description: str) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    chart_prompt = (
        f"Сгенерируй JSON-спецификацию инфографики по описанию:\n\n{description}\n\n"
        f"Верни ТОЛЬКО JSON-объект без markdown и текста вокруг. "
        f'Структура: {{"theme": "dark_modern|light_minimal|ocean|retro", "title": "...", "subtitle": "...", '
        f'"blocks": [{{"type": "heading"|"text"|"divider"|"bar"|"line"|"pie"|"pie3d"|"table", ...}}]}}'
    )
    raw = await ask_ai_async(
        prompt=chart_prompt,
        system_instruction_override=(
            "You are a data-visualization JSON generator. Output ONLY valid JSON. No markdown, no prose."
        ),
        chat_id=chat_id, user_id=user_id, platform="ds",
    )
    spec = None
    try:
        spec = json.loads(clean_json_text(raw))
    except Exception:
        m = re.search(r'\{[\s\S]*\}', raw or "")
        if m:
            try:
                spec = json.loads(m.group(0))
            except Exception:
                spec = None
    if not isinstance(spec, dict):
        await interaction.followup.send(_t(lang, "chart_error", "invalid JSON"))
        return
    try:
        img = await render_infographic(spec, user_images=None)
    except Exception as e:
        await interaction.followup.send(_t(lang, "chart_error", str(e)))
        return
    try:
        await interaction.followup.send(
            content=(spec.get("title") or _t(lang, "chart_built"))[:1900],
            file=discord.File(fp=img, filename="infographic.png"),
        )
    except Exception as e:
        await interaction.followup.send(f"Ошибка отправки: {e}")


@ds_tree.command(name="psl", description="Looksmaxxing analysis / Оценка внешности")
@app_commands.describe(image="Photo / Фото", advice="Include advice / Показать рекомендации")
async def ds_slash_psl(interaction: discord.Interaction, image: discord.Attachment, advice: bool = False) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    try:
        img_bytes = await download_image_bytes(image.url)
        cfg = get_user_config("ds", chat_id, user_id)
        theme = cfg.get("theme", "dark")
        ai_data = await get_looksmaxxing_data(img_bytes, advice, lang=lang)
        if "error" in ai_data:
            await interaction.followup.send(ai_data['error'])
            return
        infographic = await create_infographic(img_bytes, ai_data, theme=theme, lang=lang)
        report = (
            f"**{_t(lang, 'psl_title')}**\n"
            f"{_t(lang, 'psl_gender')} {ai_data.get('gender', '?')}\n"
            f"{_t(lang, 'psl_score')} `{ai_data.get('psl', '?')}/8.0`\n"
            f"{_t(lang, 'psl_tier')} `{ai_data.get('tier', '?')}`\n"
        )
        if ai_data.get("potential"):
            report += f"{_t(lang, 'psl_potential')} `{ai_data['potential']}`\n"
        report += f"\n{ai_data.get('summary', '')}"
        if advice and ai_data.get("advice"):
            report += f"\n\n**{_t(lang, 'psl_advice')}**\n{ai_data['advice']}"
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
async def ds_slash_battle(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = _ds_lang_of(interaction)
    try:
        p1 = await download_image_bytes(image1.url)
        p2 = await download_image_bytes(image2.url)
        cfg = get_user_config("ds", chat_id, user_id)
        theme = cfg.get("theme", "dark")
        ai_data = await get_battle_data(p1, p2, lang=lang)
        if "error" in ai_data:
            await interaction.followup.send(ai_data['error'])
            return
        img = await create_battle_infographic(p1, p2, ai_data, theme=theme, lang=lang)
        winner_num = str(ai_data.get("winner", "1"))
        winner_label = _t(lang, "battle_first") if winner_num == "1" else _t(lang, "battle_second")
        report = (
            f"**{_t(lang, 'battle_title')}**\n\n"
            f"{_t(lang, 'battle_winner')} **{winner_label}**\n"
            f"{_t(lang, 'battle_reason')} {ai_data.get('reason', '')}\n\n"
            f"{_t(lang, 'battle_photo1')} PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
            f"{ai_data.get('photo1', {}).get('tier', '?')}\n"
            f"{_t(lang, 'battle_photo2')} PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
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
    guild = message.guild
    is_dm = guild is None
    chat_id = message.author.id if guild is None else guild.id
    user_id = message.author.id
    content_lower = message.content.lower()
    display_name = str(getattr(message.author, "display_name", message.author.name))
    username = message.author.name
    cfg = get_user_config("ds", chat_id, user_id)
    lang_raw = cfg.get("language", "ru")
    lang = lang_raw if isinstance(lang_raw, str) else "ru"

    if not is_dm and (content_lower.startswith("кульш обновись") or content_lower.startswith("kulsh update")):
        if message.author.id not in AUTHORIZED_UPDATERS:
            await message.reply(_t(lang, "ds_update_no_access"))
            return
        await message.reply(_t(lang, "ds_update_start"))
        try:
            repo_path = os.getenv('REPO_PATH', os.getcwd())
            status, info = await perform_safe_git_update(repo_path)
            if status == "up_to_date":
                await message.reply(_t(lang, "ds_update_uptodate", info[:1500]))
            elif status == "ok":
                await message.reply(_t(lang, "ds_update_ok", info[:1500]))
                await asyncio.sleep(2)
                os._exit(0)
            elif status == "rolled_back":
                await message.reply(_t(lang, "ds_update_rolled", info[:1500]))
            else:
                await message.reply(_t(lang, "ds_update_error", info[:1500]))
        except Exception as e:
            logger.exception("update error")
            await message.reply(_t(lang, "ds_update_error", str(e)))
        return

    if (content_lower.startswith("кульш конфиг") or
            content_lower.startswith("кульш настройки") or
            content_lower.startswith("kulsh config")):
        parts = message.content.split()
        if len(parts) == 2:
            await ds_handle_config(message, user_id)
        else:
            await ds_handle_config_param(message, user_id, parts)
        return

    # ---- поиск ----
    m = re.match(r'(?i)^(?:кульш\s+)?(?:поиск|search|найди|найти)\s+(.+)$', message.content.strip(), re.DOTALL)
    if m:
        if not cfg.get("web_search_enabled", True):
            await message.reply(_t(lang, "search_off"))
            return
        async with message.channel.typing():
            results = await web_search(m.group(1).strip(), max_results=6)
            if not results:
                await message.reply(_t(lang, "search_nothing"))
                return
            context = _format_search_results(results)
            prompt = (
                f"Пользователь искал: {m.group(1).strip()}\n\n"
                f"Результаты:\n{context}\n\n"
                f"Дай краткий ответ. Без маркеров !search, !chart."
            )
            answer = await ask_ai_async(prompt=prompt, chat_id=chat_id, user_id=user_id, platform="ds")
            full = f"🔎 **{m.group(1).strip()}**\n\n{answer or ''}"
            sources = [f"{i}. [{r.get('title', '')[:60]}]({r.get('url', '')})"
                       for i, r in enumerate(results[:4], 1)]
            if sources:
                full += "\n\n**" + _t(lang, "search_source") + ":**\n" + "\n".join(sources)
            await message.reply(full[:1900])
        return

    # ---- график ----
    m = re.match(r'(?i)^(?:кульш\s+)?(?:график|chart|инфографика|диаграмма)\s+(.+)$',
                 message.content.strip(), re.DOTALL)
    if m:
        async with message.channel.typing():
            chart_prompt = (
                f"Сгенерируй JSON-спецификацию инфографики по описанию:\n\n{m.group(1).strip()}\n\n"
                f"Верни ТОЛЬКО JSON. Структура: {{\"theme\": \"dark_modern|light_minimal|ocean|retro\", "
                f"\"title\": \"...\", \"blocks\": [{{\"type\": \"bar|line|pie|pie3d|table|heading|text|divider\", ...}}]}}"
            )
            raw = await ask_ai_async(
                prompt=chart_prompt,
                system_instruction_override="You are a data-viz JSON generator. Output only valid JSON.",
                chat_id=chat_id, user_id=user_id, platform="ds",
            )
            spec = None
            try:
                spec = json.loads(clean_json_text(raw))
            except Exception:
                mm = re.search(r'\{[\s\S]*\}', raw or "")
                if mm:
                    try:
                        spec = json.loads(mm.group(0))
                    except Exception:
                        spec = None
            if not isinstance(spec, dict):
                await message.reply(_t(lang, "chart_error", "invalid JSON"))
                return
            try:
                img = await render_infographic(spec, user_images=None)
                await message.reply(file=discord.File(fp=img, filename="infographic.png"),
                                    content=(spec.get("title") or _t(lang, "chart_built"))[:1900])
            except Exception as e:
                await message.reply(_t(lang, "chart_error", str(e)))
        return

    if content_lower.startswith("кульш донаты") or content_lower.startswith("kulsh donations"):
        top = get_top_donators()
        if not top:
            await message.reply(_t(lang, "top_donators_empty", DONATE_URL))
            return
        embed = discord.Embed(title=_t(lang, "top_donators_title"), color=0x10B981)
        for i, (name, total) in enumerate(top, 1):
            embed.add_field(name=f"{i}. {name}", value=f"{total}", inline=False)
        await message.reply(embed=embed)
        return

    if (content_lower.startswith("кульш аватарк") or
            content_lower.startswith("кульш аватар") or
            content_lower.startswith("kulsh avatar")):
        avatar_raw: str | None = await get_avatar_description_ds(message, chat_id, user_id, lang=str(lang))
        if not avatar_raw:
            await message.reply(_t(lang, "avatar_fail"))
            return
        for seg in clean_extra_text(avatar_raw):
            try:
                await message.channel.send(seg)
            except Exception as e:
                logger.warning(f"DS avatar: {e}")
        return

    if not is_dm and ("кульш логи" in content_lower or "kulsh logs" in content_lower):
        if message.author.id not in AUTHORIZED_UPDATERS:
            await message.reply(_t(lang, "ds_update_no_access"))
            return
        try:
            tail = read_log_tail(20)
            intro = _t(lang, "ds_logs_content")
            try:
                await message.reply(
                    content=f"{intro}\n```\n{tail}\n```" if len(tail) <= 1900 else intro,
                    file=discord.File('bot.log'),
                )
            except FileNotFoundError:
                await message.reply(
                    f"{intro}\n```\n{tail}\n```" if len(tail) <= 1900 else f"{intro}\n\n{tail}"
                )
                return
            if len(tail) > 1900:
                for chunk in chunk_text(tail, 1900):
                    await message.channel.send(f"```\n{chunk}\n```")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")
        return

    if not is_dm and ("кульш зайди в войс" in content_lower or "kulsh join voice" in content_lower):
        author = cast(discord.Member, message.author)
        if not (author.voice and author.voice.channel):
            await message.reply(_t(lang, "ds_voice_not_in"))
            return
        voice_channel = author.voice.channel
        if guild is None:
            return
        try:
            vc = _voice_client(guild)
            if vc and vc.is_connected():
                await vc.move_to(voice_channel)
            else:
                if VOICE_RECOGNITION_ENABLED and VOICE_RECV_AVAILABLE:
                    vc = cast(discord.VoiceClient, await voice_channel.connect(cls=voice_recv.VoiceRecvClient))
                else:
                    vc = await voice_channel.connect()
            voice_text_channels[guild.id] = message.channel
            await message.reply(_t(lang, "ds_voice_joined", voice_channel.name))
            if VOICE_RECOGNITION_ENABLED and VOICE_RECV_AVAILABLE:
                sink = RecognitionSink(ds_bot, guild, message.channel)
                cast(Any, vc).listen(sink)
                setattr(vc, "_recognition_sink", sink)
        except Exception as e:
            logger.error(f"voice: {e}")
            await message.reply(_t(lang, "ds_voice_cant_join"))
        return

    if not is_dm and ("кульш выйди из войса" in content_lower or "kulsh leave voice" in content_lower):
        vc = _voice_client(guild)
        if vc and vc.is_connected():
            if hasattr(vc, "_recognition_sink"):
                getattr(vc, "_recognition_sink").cleanup()
            await vc.disconnect()
            if guild is not None:
                voice_text_channels.pop(guild.id, None)
            await message.reply(_t(lang, "ds_voice_left"))
        else:
            await message.reply(_t(lang, "ds_voice_not_in_bot"))
        return

    if is_looksmaxxing_command(message.content) and len(message.attachments) == 0:
        add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                        message.content, message_id=message.id)
        await message.reply(_t(lang, "psl_need_photo"))
        return

    if is_battle_command(message.content) and len(message.attachments) == 0:
        add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                        message.content, message_id=message.id)
        await message.reply(_t(lang, "battle_need_photos"))
        return

    image_attachments = [a for a in message.attachments if a.content_type and a.content_type.startswith('image/')]
    video_attachments = [a for a in message.attachments if a.content_type and a.content_type.startswith('video/')]
    has_battle_cmd = is_battle_command(message.content)

    if has_battle_cmd and len(image_attachments) >= 2:
        async with message.channel.typing():
            status_msg = await message.reply(_t(lang, "battle_waiting"))
            try:
                p1 = await download_image_bytes(image_attachments[0].url)
                p2 = await download_image_bytes(image_attachments[1].url)
                theme = cfg.get("theme", "dark")
                ai_data = await get_battle_data(p1, p2, lang=lang)
                if "error" in ai_data:
                    await status_msg.edit(content=str(ai_data['error']))
                    return
                img = await create_battle_infographic(p1, p2, ai_data, theme=theme, lang=lang)
                winner_num = str(ai_data.get("winner", "1"))
                winner_label = _t(lang, "battle_first") if winner_num == "1" else _t(lang, "battle_second")
                report = (
                    f"**{_t(lang, 'battle_title')}**\n\n"
                    f"{_t(lang, 'battle_winner')} **{winner_label}**\n"
                    f"{_t(lang, 'battle_reason')} {ai_data.get('reason', '')}\n\n"
                    f"{_t(lang, 'battle_photo1')} PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
                    f"{ai_data.get('photo1', {}).get('tier', '?')}\n"
                    f"{_t(lang, 'battle_photo2')} PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
                    f"{ai_data.get('photo2', {}).get('tier', '?')}"
                )
                await message.reply(file=discord.File(fp=img, filename="battle.png"),
                                    content=report[:1900])
                await status_msg.delete()
                add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                                "[battle]", message_id=message.id)
                add_bot_memory(f"ds_{chat_id}", "[battle результат]")
            except Exception as e:
                logger.error(f"DS battle: {e}")
                await status_msg.edit(content=f"Ошибка: {e}")
        return

    has_looksmaxxing_cmd = is_looksmaxxing_command(message.content)
    if has_looksmaxxing_cmd and len(image_attachments) > 0:
        async with message.channel.typing():
            try:
                psl_bytes = await download_image_bytes(image_attachments[0].url)
                include_advice = "совет" in content_lower or "advice" in content_lower
                theme = cfg.get("theme", "dark")
                ai_data = await get_looksmaxxing_data(psl_bytes, include_advice, lang=lang)
                if "error" in ai_data:
                    await message.reply(ai_data['error'])
                    return
                infographic = await create_infographic(psl_bytes, ai_data, theme=theme, lang=lang)
                report = (
                    f"**{_t(lang, 'psl_title')}**\n"
                    f"{_t(lang, 'psl_gender')} {ai_data.get('gender', '?')}\n"
                    f"{_t(lang, 'psl_score')} `{ai_data.get('psl', '?')}/8.0`\n"
                    f"{_t(lang, 'psl_tier')} `{ai_data.get('tier', '?')}`\n"
                )
                if ai_data.get("potential"):
                    report += f"{_t(lang, 'psl_potential')} `{ai_data['potential']}`\n"
                report += f"\n{ai_data.get('summary', '')}"
                if include_advice and ai_data.get("advice"):
                    report += f"\n\n**{_t(lang, 'psl_advice')}**\n{ai_data['advice']}"
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
                media_bytes: bytes | None = None
                img_mime = "image/jpeg"
                if image_attachments:
                    media_bytes = await download_image_bytes(image_attachments[0].url)
                    img_mime = image_attachments[0].content_type or "image/jpeg"
                elif video_attachments:
                    vid = await download_image_bytes(video_attachments[0].url)
                    frame = await extract_video_frame(vid, ".mp4")
                    if frame:
                        media_bytes = frame
                prompt = message.content.strip() or ("че на этом?" if lang == "ru" else "what's this?")
                add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                                f"{prompt} [с медиа]",
                                ["photo" if image_attachments else "video"],
                                message_id=message.id)
                messages = memory_to_messages(get_chat_memory(f"ds_{chat_id}"))
                answer = await ask_ai_async(messages=messages, image_bytes=media_bytes,
                                            image_mime=img_mime, chat_id=chat_id,
                                            user_id=user_id, platform="ds")
                await send_ds_ai_response(message, chat_id, user_id, answer, user_text=prompt)
                asyncio.create_task(extract_memory(f"ds_{chat_id}", f"{display_name}: [медиа]", answer))
            except Exception as e:
                logger.info(f"DS media: {e}")
                await message.reply(_t(lang, "ds_attachments_error"))
        return

    if addressed:
        async with message.channel.typing():
            add_user_memory(f"ds_{chat_id}", "DS", display_name, username, user_id,
                            message.content, message_id=message.id)
            messages = memory_to_messages(get_chat_memory(f"ds_{chat_id}"))
            answer = await ask_ai_async(messages=messages, chat_id=chat_id,
                                        user_id=user_id, platform="ds")
            await send_ds_ai_response(message, chat_id, user_id, answer, user_text=message.content)
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
            if answer and answer.strip() and answer.strip().upper() not in ("НЕТ", "NO"):
                last_random_reply[f"ds_{chat_id}"] = time.time()
                await send_ds_ai_response(message, chat_id, user_id, answer)
        except Exception as e:
            logger.warning(f"DS random reply: {e}")

# ============================================================
# DONATION ALERTS
# ============================================================
async def send_donation_alert(platform: str, name: str, amount: int, message_text: str = '') -> None:
    if platform == 'tg':
        text = f"🍷🗿 {name} задонатил {amount} звёзд! Спасибо!"
        if message_text:
            text += f"\nСообщение: {message_text}"
        try:
            await send_tg_html(TG_TARGET_CHAT, text)
        except Exception as e:
            logger.error(f"Донат в ТГ: {e}")
    elif platform == 'ds':
        text = f"💎 {name} задонатил {amount} руб."
        if message_text:
            text += f"\n> {message_text}"
        if DS_DONATION_CHANNEL_ID:
            channel = ds_bot.get_channel(DS_DONATION_CHANNEL_ID)
            sendable = _messageable(cast(discord.abc.Messageable | None, channel))
            if sendable is not None:
                try:
                    await sendable.send(text)
                except Exception as e:
                    logger.error(f"Донат в DS: {e}")


async def donation_alerts_listener() -> None:
    if not DONATIONALERTS_TOKEN:
        logger.info("🔕 DonationAlerts токен не задан.")
        return
    await ds_bot.wait_until_ready()
    sio = socketio.AsyncClient(query={'token': DONATIONALERTS_TOKEN})

    @cast(Callable[[_HandlerT], _HandlerT], sio.event)
    async def connect() -> None:
        logger.info("🔌 DonationAlerts подключён")

    @cast(Callable[[_HandlerT], _HandlerT], sio.event)
    async def disconnect() -> None:
        logger.warning("🔌 DonationAlerts отключён")

    @cast(Callable[[_HandlerT], _HandlerT], sio.on('donation'))
    async def on_donation(data: JsonDict) -> None:
        try:
            amount = float(cast(Any, data.get('amount', 0)))
            currency = str(data.get('currency', 'RUB'))
            if currency != 'RUB':
                return
            points = int(amount)
            username = str(data.get('username', 'Аноним'))
            message = str(data.get('message', ''))
            logger.info(f"💰 {username} → {points}")
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
    class RecognitionSink(voice_recv.AudioSink):  # type: ignore[misc]
        def __init__(
            self,
            bot: discord.Client,
            guild: discord.Guild,
            text_channel: discord.abc.Messageable,
        ) -> None:
            super().__init__()
            self.bot = bot
            self.guild = guild
            self.text_channel = text_channel
            self.buffers: dict[int | str, bytearray] = {}
            self.recognizer = sr.Recognizer()
            self.processing_tasks: dict[int | str, Any] = {}

        def wants_opus(self) -> bool:
            return False

        def write(self, user: discord.User | None, data: Any) -> None:
            user_id = user.id if user else "unknown_session"
            user_name = user.name if user else "Аноним"
            if user and user.bot:
                return
            if user_id not in self.buffers:
                self.buffers[user_id] = bytearray()
            self.buffers[user_id].extend(cast(bytes, data.pcm))
            if len(self.buffers[user_id]) > 380000:
                if user_id in self.processing_tasks:
                    self.processing_tasks[user_id].cancel()
                self.processing_tasks[user_id] = asyncio.run_coroutine_threadsafe(
                    self.wait_and_process(user_id, user_name), self.bot.loop
                )

        def _sync_recognize(self, pcm_data: bytes) -> str | None:
            try:
                audio = AudioSegment(data=pcm_data, sample_width=2, frame_rate=48000,
                                     channels=2).set_channels(1).set_frame_rate(16000)
                wav_io = BytesIO()
                audio.export(wav_io, format="wav")
                wav_io.seek(0)
                with sr.AudioFile(wav_io) as source:
                    recognized = self.recognizer.recognize_google(
                        self.recognizer.record(source), language="ru-RU"
                    )
                    return recognized if isinstance(recognized, str) else None
            except sr.UnknownValueError:
                return None
            except Exception as e:
                logger.error(f"recognize: {e}")
                return None

        async def wait_and_process(self, user_id: int | str, user_name: str) -> None:
            try:
                await asyncio.sleep(1.5)
                if user_id in self.buffers:
                    pcm_data = bytes(self.buffers.pop(user_id))
                    text = await asyncio.to_thread(self._sync_recognize, pcm_data)
                    if text and random.random() <= 0.65:
                        logger.info(f"🎤 Распознано: {text}")
            except asyncio.CancelledError:
                pass

        def cleanup(self) -> None:
            for task in self.processing_tasks.values():
                task.cancel()
            self.buffers.clear()
else:
    class RecognitionSink:  # type: ignore[no-redef]
        pass

# ============================================================
# TTS
# ============================================================
async def say_in_voice(voice_client: discord.VoiceClient | None, text: str) -> None:
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
            if not answer or not answer.strip() or answer.strip().upper() in ("НЕТ", "NO"):
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
            prompt = ("Попроси Антона отправить Фолзу сообщение в TikTok чтобы продлить серию. "
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
            logger.info("ℹ️ Распознавание голоса отключено")

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
    logger.info(f">>> 🍷🗿 Кульш в эфире. МСК: {msk_datetime_str()}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
