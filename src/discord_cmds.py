# Kulsh GPT | v2.39.0
# by (main author): starfall-apk
# coauthor & bot hosting: pomidorka1515

"""Discord slash commands and channel-config helpers.

Commands are plain coroutines. app.register_discord() attaches them to the tree.
"""

import asyncio
import json
import random
import re
from typing import Any

import discord
from discord import app_commands

from src.ai import extract_search_marker, format_search_results, ask_ai_async, web_search
from src.charts import extract_chart_marker, render_infographic
from src.looks import create_battle_infographic, create_infographic, get_battle_data, get_looksmaxxing_data
from src.util import (
    DAILY_CREDITS,
    DONATE_URL,
    GITHUB_URL,
    MINI_APP_URL,
    MODEL_DISPLAY,
    MODEL_LIST,
    ds_user,
    json_str,
    tr,
    add_bot_memory,
    chat_media_history,
    download_image_bytes,
    get_user_config,
    get_user_credits,
    logger,
    model_display_name,
    process_ai_response,
    read_log_tail,

    AUTHORIZED_UPDATERS,
    GIF_POOL,
    as_member,
    calc_typing_delay,
    clean_extra_text,
    clean_json_text,
    premium_functions_enabled,)

ds_bot: Any = None


def bind(bot: Any) -> None:
    global ds_bot
    ds_bot = bot

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

async def get_avatar_description_ds(
    message: discord.Message, chat_id: int, user_id: int, lang: str = "ru",
) -> str | None:
    target = None
    me = ds_user(ds_bot)
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
        desc = json_str(await ask_ai_async(
            prompt=prompt, image_bytes=img_bytes, image_mime="image/jpeg",
            chat_id=chat_id, user_id=user_id, platform="ds",
        ))
        return desc or None
    except Exception as e:
        logger.warning(f"DS avatar desc: {e}")
        return None

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

async def send_ds_ai_response(message: discord.Message, chat_id: int, user_id: int,
                              answer_raw: str, user_text: str | None = None) -> None:
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    separate_enabled = cfg.get("separate_enabled", True)

    # !search
    if cfg.get("web_search_enabled", True):
        query, _ = extract_search_marker(answer_raw or "")
        if query:
            results = await web_search(query, max_results=6)
            if results:
                context = format_search_results(results)
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
                answer_raw = tr(lang, "search_nothing")

    # !chart
    if premium_functions_enabled:
        chart_spec, remaining = extract_chart_marker(answer_raw or "")
        if chart_spec:
            try:
                img = await render_infographic(chart_spec, user_images=None)
                try:
                    await message.reply(file=discord.File(fp=img, filename="infographic.png"),
                                        content=(chart_spec.get("title") or tr(lang, "chart_built"))[:1900])
                except Exception as e:
                    logger.error(f"ds chart send: {e}")
                answer_raw = remaining
            except Exception as e:
                logger.error(f"ds chart render: {e}")
                answer_raw = remaining + "\n" + tr(lang, "chart_error", str(e))

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
def ds_config_embed(chat_id: int, user_id: int) -> discord.Embed:
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    series = tr(lang, "on") if cfg.get("series_reminder_enabled", True) else tr(lang, "off")
    stickers = tr(lang, "on") if cfg.get("stickers_enabled", True) else tr(lang, "off")
    sep = tr(lang, "on") if cfg.get("separate_enabled", True) else tr(lang, "off")
    autoreply = tr(lang, "on") if cfg.get("random_reply_enabled", False) else tr(lang, "off")
    random_msgs = tr(lang, "on") if cfg.get("random_messages_enabled", True) else tr(lang, "off")
    websearch = tr(lang, "on") if cfg.get("web_search_enabled", True) else tr(lang, "off")
    prompt = cfg.get("custom_prompt") or ("стандартный" if lang == "ru" else "default")
    if len(prompt) > 900:
        prompt = prompt[:900] + "..."
    theme_disp = tr(lang, "dark") if cfg.get("theme", "dark") == "dark" else tr(lang, "light")
    lang_disp = tr(lang, "russian") if lang == "ru" else tr(lang, "english")

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
    member = as_member(message.author)
    if message.guild and not (member and member.guild_permissions.administrator):
        cfg = get_user_config("ds", chat_id, user_id)
        lang = cfg.get("language", "ru")
        await message.reply(tr(lang, "ds_only_admins"))
        return
    embed = ds_config_embed(chat_id, user_id)
    await message.reply(embed=embed)


async def ds_handle_config_param(message: discord.Message, user_id: int, parts: list[str]) -> None:
    chat_id = message.channel.id
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    member = as_member(message.author)
    if message.guild and not (member and member.guild_permissions.administrator):
        await message.reply(tr(lang, "ds_only_admins"))
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
            await message.reply(tr("ru", "ds_setting_lang", tr("ru", "russian")))
        elif val in ("en", "английский", "english"):
            cfg["language"] = "en"
            await message.reply(tr("en", "ds_setting_lang", tr("en", "english")))
        else:
            await message.reply(tr(lang, "ds_need_specify_ru_en"))
    elif param in ("тема", "theme"):
        if val in ("тёмная", "темная", "dark"):
            cfg["theme"] = "dark"
            await message.reply(tr(lang, "ds_setting_theme", tr(lang, "dark")))
        elif val in ("светлая", "light"):
            cfg["theme"] = "light"
            await message.reply(tr(lang, "ds_setting_theme", tr(lang, "light")))
        else:
            await message.reply(tr(lang, "ds_need_specify_theme"))
    elif param in ("серия", "series"):
        cfg["series_reminder_enabled"] = bool_on
        await message.reply(tr(lang, "ds_setting_series", tr(lang, "on") if bool_on else tr(lang, "off")))
    elif param in ("стикеры", "stickers"):
        cfg["stickers_enabled"] = bool_on
        await message.reply(tr(lang, "ds_setting_stickers", tr(lang, "on") if bool_on else tr(lang, "off")))
    elif param in ("разбивка", "split"):
        cfg["separate_enabled"] = bool_on
        await message.reply(tr(lang, "ds_setting_sep", tr(lang, "on") if bool_on else tr(lang, "off")))
    elif param in ("автоответ", "autoreply"):
        cfg["random_reply_enabled"] = bool_on
        await message.reply(tr(lang, "ds_setting_autoreply", tr(lang, "on") if bool_on else tr(lang, "off")))
    elif param in ("рандом", "random"):
        cfg["random_messages_enabled"] = bool_on
        await message.reply(tr(lang, "ds_setting_random", tr(lang, "on") if bool_on else tr(lang, "off")))
    elif param in ("поиск", "search"):
        cfg["web_search_enabled"] = bool_on
        await message.reply(tr(lang, "ds_setting_websearch", tr(lang, "on") if bool_on else tr(lang, "off")))
    elif param in ("температура", "temperature"):
        try:
            t = max(0.0, min(2.0, float(val)))
            cfg["temperature"] = t
            await message.reply(tr(lang, "ds_setting_temp", t))
        except ValueError:
            await message.reply(tr(lang, "ds_setting_temp_bad"))
    elif param in ("промпт", "prompt"):
        new_prompt = " ".join(parts[3:]).strip()
        if new_prompt.lower() in ("сброс", "reset", "убрать", "стандарт", "default"):
            cfg["custom_prompt"] = None
            await message.reply(tr(lang, "ds_setting_prompt_reset"))
        elif new_prompt:
            cfg["custom_prompt"] = new_prompt[:2000]
            await message.reply(tr(lang, "ds_setting_prompt_set"))
        else:
            await message.reply(tr(lang, "ds_setting_prompt_need"))
    elif param in ("модель", "model"):
        if not val:
            lines = [f"`{i}` — {MODEL_DISPLAY.get(m, m)}" for i, m in enumerate(MODEL_LIST)]
            await message.reply(
                f"{tr(lang, 'ds_setting_model', model_display_name(cfg.get('model'), lang))}\n\n" + "\n".join(lines)
            )
        elif val in ("авто", "auto"):
            cfg["model"] = None
            await message.reply(tr(lang, "ds_setting_model_auto"))
        else:
            try:
                idx = int(val)
                if 0 <= idx < len(MODEL_LIST):
                    cfg["model"] = MODEL_LIST[idx]
                    await message.reply(tr(lang, "ds_setting_model",
                                            MODEL_DISPLAY.get(MODEL_LIST[idx], MODEL_LIST[idx])))
                else:
                    await message.reply(tr(lang, "ds_setting_model_badnum"))
            except ValueError:
                await message.reply(tr(lang, "ds_setting_model_bad"))
    else:
        await message.reply(tr(lang, "ds_unknown_param"))

def ds_slash_help(lang: str) -> str:
    return tr(lang, "help_body", MINI_APP_URL, GITHUB_URL)


def ds_slash_menu(lang: str) -> str:
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


def ds_slash_start(lang: str) -> str:
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


def ds_lang_of(interaction: discord.Interaction) -> str:
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    cfg = get_user_config("ds", chat_id, user_id)
    lang = cfg.get("language", "ru")
    return lang if isinstance(lang, str) else "ru"


async def ds_slash_start(interaction: discord.Interaction) -> None:
    lang = ds_lang_of(interaction)
    await interaction.response.send_message(ds_slash_start(lang))


async def ds_slash_menu(interaction: discord.Interaction) -> None:
    lang = ds_lang_of(interaction)
    await interaction.response.send_message(ds_slash_menu(lang))


async def ds_slash_help(interaction: discord.Interaction) -> None:
    lang = ds_lang_of(interaction)
    await interaction.response.send_message(ds_slash_help(lang))


async def ds_slash_donate(interaction: discord.Interaction) -> None:
    lang = ds_lang_of(interaction)
    text = (
        f"# {tr(lang, 'donate_title')}\n\n"
        f"✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"{tr(lang, 'donate_intro')}\n\n"
        f"▸ {tr(lang, 'donate_online')}: {DONATE_URL}\n"
        f"🔗 GitHub: {GITHUB_URL}"
    )
    await interaction.response.send_message(text)


async def ds_slash_credits(interaction: discord.Interaction) -> None:
    lang = ds_lang_of(interaction)
    creds = get_user_credits("ds", interaction.user.id)
    await interaction.response.send_message(tr(lang, "credits_balance", creds, DAILY_CREDITS))


async def ds_slash_config(interaction: discord.Interaction) -> None:
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
    member = as_member(interaction.user)
    if interaction.guild and not (member and member.guild_permissions.administrator):
        await interaction.response.send_message(tr(lang, "ds_only_admins"), ephemeral=True)
        return
    embed = ds_config_embed(chat_id, user_id)
    await interaction.response.send_message(embed=embed)


@app_commands.describe(user="Whose avatar to describe / Чью аватарку описать")
async def ds_slash_avatar(interaction: discord.Interaction, user: discord.Member | None = None) -> None:
    await interaction.response.defer()
    target = user or interaction.user
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
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
            await interaction.followup.send(tr(lang, "avatar_fail"))
            return
        for seg in segments:
            await interaction.followup.send(seg)
    except Exception as e:
        logger.error(f"DS slash avatar: {e}")
        await interaction.followup.send(f"Ошибка: {e}")


@app_commands.describe(count="How many last items / Сколько последних элементов")
async def ds_slash_recall(interaction: discord.Interaction, count: int = 3) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
    n = max(1, min(10, count))
    history = list(chat_media_history.get(f"ds_{chat_id}", []))
    if not history:
        await interaction.followup.send(tr(lang, "recall_fail"))
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


async def ds_slash_logs(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    lang = ds_lang_of(interaction)
    if interaction.user.id not in AUTHORIZED_UPDATERS:
        await interaction.followup.send(tr(lang, "ds_update_no_access"), ephemeral=True)
        return
    try:
        tail = read_log_tail(20)
        intro = tr(lang, "ds_logs_content")
        content = f"{intro}\n```\n{tail}\n```" if len(tail) <= 1900 else f"{intro}\n\n{tail[:1900]}"
        try:
            await interaction.followup.send(content=content, file=discord.File('bot.log'), ephemeral=True)
        except FileNotFoundError:
            await interaction.followup.send(content=content, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}", ephemeral=True)


@app_commands.describe(query="What to search / Что искать")
async def ds_slash_search(interaction: discord.Interaction, query: str) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
    cfg = get_user_config("ds", chat_id, user_id)
    if not cfg.get("web_search_enabled", True):
        await interaction.followup.send(tr(lang, "search_off"))
        return
    results = await web_search(query, max_results=6)
    if not results:
        await interaction.followup.send(tr(lang, "search_nothing"))
        return
    context = format_search_results(results)
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
        full += "\n\n**" + tr(lang, "search_source") + ":**\n" + "\n".join(sources)
    await interaction.followup.send(full[:1900])


@app_commands.describe(description="Describe the chart / Опиши график")
async def ds_slash_chart(interaction: discord.Interaction, description: str) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
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
        await interaction.followup.send(tr(lang, "chart_error", "invalid JSON"))
        return
    try:
        img = await render_infographic(spec, user_images=None)
    except Exception as e:
        await interaction.followup.send(tr(lang, "chart_error", str(e)))
        return
    try:
        await interaction.followup.send(
            content=(spec.get("title") or tr(lang, "chart_built"))[:1900],
            file=discord.File(fp=img, filename="infographic.png"),
        )
    except Exception as e:
        await interaction.followup.send(f"Ошибка отправки: {e}")


@app_commands.describe(image="Photo / Фото", advice="Include advice / Показать рекомендации")
async def ds_slash_psl(interaction: discord.Interaction, image: discord.Attachment, advice: bool = False) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
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
            f"**{tr(lang, 'psl_title')}**\n"
            f"{tr(lang, 'psl_gender')} {ai_data.get('gender', '?')}\n"
            f"{tr(lang, 'psl_score')} `{ai_data.get('psl', '?')}/8.0`\n"
            f"{tr(lang, 'psl_tier')} `{ai_data.get('tier', '?')}`\n"
        )
        if ai_data.get("potential"):
            report += f"{tr(lang, 'psl_potential')} `{ai_data['potential']}`\n"
        report += f"\n{ai_data.get('summary', '')}"
        if advice and ai_data.get("advice"):
            report += f"\n\n**{tr(lang, 'psl_advice')}**\n{ai_data['advice']}"
        await interaction.followup.send(
            content=report[:1900],
            file=discord.File(fp=infographic, filename="psl.png"),
        )
        if len(report) > 1900:
            await interaction.followup.send(report[1900:])
    except Exception as e:
        logger.error(f"DS slash psl: {e}")
        await interaction.followup.send(f"Ошибка: {e}")


@app_commands.describe(image1="First photo / Первое фото", image2="Second photo / Второе фото")
async def ds_slash_battle(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment) -> None:
    await interaction.response.defer()
    chat_id = interaction.channel_id or 0
    user_id = interaction.user.id
    lang = ds_lang_of(interaction)
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
        winner_label = tr(lang, "battle_first") if winner_num == "1" else tr(lang, "battle_second")
        report = (
            f"**{tr(lang, 'battle_title')}**\n\n"
            f"{tr(lang, 'battle_winner')} **{winner_label}**\n"
            f"{tr(lang, 'battle_reason')} {ai_data.get('reason', '')}\n\n"
            f"{tr(lang, 'battle_photo1')} PSL {ai_data.get('photo1', {}).get('psl', '?')} | "
            f"{ai_data.get('photo1', {}).get('tier', '?')}\n"
            f"{tr(lang, 'battle_photo2')} PSL {ai_data.get('photo2', {}).get('psl', '?')} | "
            f"{ai_data.get('photo2', {}).get('tier', '?')}"
        )
        await interaction.followup.send(
            content=report[:1900],
            file=discord.File(fp=img, filename="battle.png"),
        )
    except Exception as e:
        logger.error(f"DS slash battle: {e}")
        await interaction.followup.send(f"Ошибка: {e}")

