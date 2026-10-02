# Kulsh GPT | v2.40.1
# by (main author): starfall-apk
# coauthor & bot hosting: pomidorka1515

"""Telegram keyboards, callbacks, and message handlers."""

import asyncio
from collections import deque
import html
import json
import random
import re
import time
from typing import Any, cast

import telebot
from telebot.types import ForceReply, InlineKeyboardMarkup, InputFile

from src.loops import send_donation_alert
from src.ai import (
    extract_search_marker,
    format_search_results,
    ask_ai_async,
    web_search,
    user_wants_chart,
)
from src.charts import extract_chart_marker, render_infographic
from src.looks import (
    create_femboy_battle_infographic,
    create_femboy_infographic,
    get_femboy_battle_data,
    get_femboy_data,
)
from src.rich import (
    cleanup_config_children,
    edit_rich_message,
    play_apply_animation,
    reply_tg_html,
    send_formatted,
    send_rich_message,
    send_tg_html,
    stream_draft,
    typing_with_delay_tg,
)
from src.ui import (
    build_menu_text,
    build_start_text,
    config_text,
    model_picker_text,
    mode_picker_text,
    build_lang_keyboard,
    build_main_config_keyboard,
    build_menu_keyboard,
    build_mode_keyboard,
    build_model_keyboard,
    build_start_keyboard,
    build_temp_keyboard,
    build_theme_keyboard,
)
from src.util import (
    BOT_VERSION,
    COMMUNICATION_MODES,
    DAILY_CREDITS,
    DONATE_URL,
    GITHUB_URL,
    MINI_APP_URL,
    MODEL_DISPLAY,
    MODEL_LIST,
    PREMIUM_ADMIN_ID,
    STICKER_POOL,
    UTILITY_PATTERNS,
    cb_id,
    human_uptime,
    is_femboy_battle_command,
    is_femboy_rate_command,
    mode_is_valid,
    tr,
    tg_msg,
    add_bot_memory,
    add_donation,
    chat_media_history,
    chat_memories,
    clean_extra_text,
    clean_json_text,
    config_children_msgs,
    config_msg_owners,
    config_trigger_msgs,
    get_chat_key,
    get_chat_memory,
    get_user_config,
    get_user_credits,
    last_old_reply,
    last_random_reply,
    logger,
    long_term_memory,
    pending_donations,
    process_ai_response,
    prompt_waiting,
    save_long_term_memory,
    user_femboy_state,
)
import src.util as state

tg_bot: Any = None


def _media():
    from src import media as media_mod
    return media_mod


async def get_avatar_description_tg(message: telebot.types.Message, chat_id: int, user_id: int, lang: str = "ru") -> str | None:
    return await _media().get_avatar_description_tg(message, chat_id, user_id, lang)


async def get_recall_media_description_tg(
    message: telebot.types.Message, chat_id: int, user_id: int, n: int = 3, lang: str = "ru",
) -> str | None:
    return await _media().get_recall_media_description_tg(message, chat_id, user_id, n, lang)


def bind(bot: Any) -> None:
    global tg_bot
    tg_bot = bot
    from src import rich
    rich.bind(bot)


def _strip_recall_marker(text: str) -> str:
    """Удаляет !recall_media из текста без побочных эффектов."""
    if not text:
        return text
    pat = UTILITY_PATTERNS.get("recall_media")
    if pat is None:
        return text
    out = pat.sub(' ', text)
    out = re.sub(r'[ \t]{2,}', ' ', out)
    out = re.sub(r'[ \t]+([,.!?;:])', r'\1', out)
    out = re.sub(r'[ \t]+\n', '\n', out)
    return out.strip()


# ============================================================
# CALLBACK HANDLER (cfg:)
# ============================================================
async def edit_or_send(call: telebot.types.CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    msg = tg_msg(call)
    try:
        await tg_bot.edit_message_text(
            text, msg.chat.id, msg.message_id,
            parse_mode='HTML', reply_markup=kb,
        )
    except Exception as e:
        logger.warning(f"edit_message_text fail: {e}")


async def handle_cfg_callback(call: telebot.types.CallbackQuery) -> None:
    msg = tg_msg(call)
    data = call.data or ""
    owner = config_msg_owners.get(msg.message_id)
    if owner is not None and owner != call.from_user.id:
        l = get_user_config("tg", msg.chat.id, call.from_user.id).get("language", "ru")
        await tg_bot.answer_callback_query(cb_id(call), tr(l, "cfg_not_yours"), show_alert=False)
        return

    chat_id = msg.chat.id
    user_id = call.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    toast = tr(lang, "cfg_updated")
    is_private = (msg.chat.type == 'private')

    if action == "mode":
        await edit_or_send(call, mode_picker_text("tg", chat_id, user_id, is_private=is_private),
                            build_mode_keyboard("tg", chat_id, user_id, is_private=is_private))
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "mode_set":
        value = parts[2] if len(parts) > 2 else "kent"
        if value == "pro" and not is_private:
            await tg_bot.answer_callback_query(cb_id(call), tr(lang, "mode_need_dm"), show_alert=True)
            return
        if value in COMMUNICATION_MODES:
            cfg["communication_mode"] = value
            if value == "assistant":
                toast = tr(lang, "mode_set", tr(lang, "mode_assistant"))
            elif value == "pro":
                toast = tr(lang, "mode_set", tr(lang, "mode_pro"))
            else:
                toast = tr(lang, "mode_set", tr(lang, "mode_kent"))
        await edit_or_send(call, config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call), toast)
        return

    if action == "model_set":
        value = parts[2] if len(parts) > 2 else "auto"
        if value == "auto":
            cfg["model"] = None
            toast = tr(lang, "cfg_model_auto")
        else:
            try:
                idx = int(value)
                if 0 <= idx < len(MODEL_LIST):
                    cfg["model"] = MODEL_LIST[idx]
                    toast = tr(lang, "cfg_model_set", MODEL_DISPLAY.get(MODEL_LIST[idx], MODEL_LIST[idx]))
            except ValueError:
                pass
        await edit_or_send(call, model_picker_text("tg", chat_id, user_id),
                            build_model_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call), toast)
        return

    if action == "model":
        await edit_or_send(call, model_picker_text("tg", chat_id, user_id),
                            build_model_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action in ("model_back", "sub_back"):
        await edit_or_send(call, config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "lang":
        await edit_or_send(call, f"<b>{tr(lang, 'cfg_lang')}</b>", build_lang_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "lang_set":
        val = parts[2] if len(parts) > 2 else "ru"
        if val in ("ru", "en"):
            cfg["language"] = val
            lang = val
            toast = tr(lang, "cfg_lang_set_ru") if val == "ru" else tr(lang, "cfg_lang_set_en")
        await edit_or_send(call, config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call), toast)
        return

    if action == "theme":
        await edit_or_send(call, f"<b>{tr(lang, 'cfg_theme')}</b>", build_theme_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "theme_set":
        val = parts[2] if len(parts) > 2 else "dark"
        if val in ("dark", "light"):
            cfg["theme"] = val
            toast = tr(lang, "cfg_theme_dark") if val == "dark" else tr(lang, "cfg_theme_light")
        await edit_or_send(call, config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call), toast)
        return

    if action == "temp":
        await edit_or_send(call, f"<b>{tr(lang, 'cfg_temp_short')}</b>",
                            build_temp_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "temp_set":
        try:
            temp_val = max(0.0, min(2.0, float(parts[2])))
            cfg["temperature"] = temp_val
            toast = tr(lang, "cfg_temp", temp_val)
        except (ValueError, IndexError):
            pass
        await edit_or_send(call, config_text("tg", chat_id, user_id),
                            build_main_config_keyboard("tg", chat_id, user_id))
        await tg_bot.answer_callback_query(cb_id(call), toast)
        return

    if action == "prompt":
        try:
            sent = await tg_bot.send_message(
                chat_id, tr(lang, "cfg_edit_prompt_ask"),
                parse_mode='HTML',
                reply_markup=ForceReply(selective=True),
                reply_to_message_id=msg.message_id,
            )
            prompt_waiting[user_id] = sent.message_id
            key = (chat_id, user_id)
            config_children_msgs.setdefault(key, []).append(sent.message_id)
        except Exception as e:
            logger.warning(f"prompt ask fail: {e}")
        await tg_bot.answer_callback_query(cb_id(call))
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
        await cleanup_config_children(chat_id, user_id)
        await tg_bot.answer_callback_query(cb_id(call), tr(lang, "cfg_done"))
        asyncio.create_task(play_apply_animation(chat_id, msg.message_id))
        return

    if action == "separate":
        new_val = not cfg.get("separate_enabled", True)
        if new_val and cfg.get("streaming_enabled", False):
            await tg_bot.answer_callback_query(cb_id(call), tr(lang, "cfg_mutex"), show_alert=False)
            return
        cfg["separate_enabled"] = new_val
    elif action == "streaming":
        if not state.premium_functions_enabled:
            await tg_bot.answer_callback_query(cb_id(call), tr(lang, "cfg_premium_off"), show_alert=False)
            return
        new_val = not cfg.get("streaming_enabled", False)
        if new_val and cfg.get("separate_enabled", True):
            await tg_bot.answer_callback_query(cb_id(call), tr(lang, "cfg_mutex"), show_alert=False)
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
        toast = tr(lang, "cfg_prompt_reset")
    elif action == "reset_memory":
        chat_key = f"tg_{chat_id}"
        if chat_key in long_term_memory:
            del long_term_memory[chat_key]
            save_long_term_memory(long_term_memory)
        chat_memories[chat_key] = deque(maxlen=20)
        chat_media_history[chat_key].clear()
        last_random_reply.pop(chat_key, None)
        last_old_reply.pop(chat_key, None)
        toast = tr(lang, "cfg_memory_reset")

    await edit_or_send(call, config_text("tg", chat_id, user_id),
                        build_main_config_keyboard("tg", chat_id, user_id))
    await tg_bot.answer_callback_query(cb_id(call), toast)


# ============================================================
# CALLBACK HANDLER (menu:)
# ============================================================
async def handle_menu_callback(call: telebot.types.CallbackQuery) -> None:
    msg = tg_msg(call)
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
        await cleanup_config_children(chat_id, user_id)
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "settings":
        cfg_text = config_text("tg", chat_id, user_id)
        kb = build_main_config_keyboard("tg", chat_id, user_id)
        try:
            await tg_bot.edit_message_text(
                cfg_text, chat_id, msg.message_id,
                parse_mode='HTML', reply_markup=kb,
            )
            config_msg_owners[msg.message_id] = user_id
        except Exception as e:
            logger.warning(f"menu:settings edit: {e}")
        await tg_bot.answer_callback_query(cb_id(call))
        return

    if action == "help":
        await tg_bot.answer_callback_query(cb_id(call))
        help_text = tr(lang, "help_body", MINI_APP_URL, GITHUB_URL)
        edited = await edit_rich_message(chat_id, msg.message_id, help_text)
        if not edited:
            try:
                await tg_bot.delete_message(chat_id, msg.message_id)
            except Exception:
                pass
            await send_formatted(chat_id, help_text)
        return

    if action == "open":
        await tg_bot.answer_callback_query(cb_id(call))
        menu_text = build_menu_text(lang)
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
# TELEGRAM: HELP / MENU / START / DONATE / STATUS
# ============================================================
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

    start_text = build_start_text(lang)
    kb = build_start_keyboard(lang, is_private=is_private)
    await send_formatted(chat_id, start_text, reply_to=message.message_id, reply_markup=kb)


async def handle_menu(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    is_private = (message.chat.type == 'private')

    menu_text = build_menu_text(lang)
    kb = build_menu_keyboard(lang, is_private=is_private)
    await send_formatted(chat_id, menu_text, reply_to=message.message_id, reply_markup=kb)


async def handle_help(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    cfg = get_user_config("tg", message.chat.id, message.from_user.id)
    lang = cfg.get("language", "ru")
    help_text = tr(lang, "help_body", MINI_APP_URL, GITHUB_URL)
    try:
        await send_formatted(message.chat.id, help_text, reply_to=message.message_id)
    except Exception:
        await tg_bot.send_message(
            message.chat.id, re.sub(r'<[^>]+>', '', help_text),
            reply_to_message_id=message.message_id,
        )


async def handle_donate(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    cfg = get_user_config("tg", message.chat.id, message.from_user.id)
    lang = cfg.get("language", "ru")
    text = (
        f"# {tr(lang, 'donate_title')}\n\n"
        f"✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"{tr(lang, 'donate_intro')}\n\n"
        f"**{tr(lang, 'donate_methods')}**\n\n"
        f"- {tr(lang, 'donate_online')}: {DONATE_URL}\n"
        f"- {tr(lang, 'donate_stars_hint')}\n\n"
        f"🔗 GitHub: {GITHUB_URL}"
    )
    try:
        await send_formatted(message.chat.id, text, reply_to=message.message_id)
    except Exception:
        await reply_tg_html(message, f"Поддержать Кульша: {DONATE_URL} 🍷🗿")


async def handle_donate_stars(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    cfg = get_user_config("tg", chat_id, message.from_user.id)
    lang = cfg.get("language", "ru")
    args = (telebot.util.extract_arguments(message.text or "") or "").strip()
    if not args:
        await reply_tg_html(message, tr(lang, "donate_stars_need"))
        return
    try:
        stars = int(args.split()[0])
        if stars <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await reply_tg_html(message, tr(lang, "donate_stars_bad"))
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
        await reply_tg_html(message, tr(lang, "donate_invoice_fail", str(e)))


async def handle_credits(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    cfg = get_user_config("tg", message.chat.id, message.from_user.id)
    lang = cfg.get("language", "ru")
    creds = get_user_credits("tg", message.from_user.id)
    await reply_tg_html(message, tr(lang, "credits_balance", creds, DAILY_CREDITS))


async def handle_status(message: telebot.types.Message) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    cfg = get_user_config("tg", chat_id, message.from_user.id)
    lang = cfg.get("language", "ru")
    mode_txt = str(cfg.get("communication_mode", "kent"))
    if mode_txt == "assistant":
        mode_label = tr(lang, "mode_assistant")
    elif mode_txt == "pro":
        mode_label = tr(lang, "mode_pro")
    else:
        mode_label = tr(lang, "mode_kent")

    try:
        proc_load = __import__("os").getloadavg()[0]
    except Exception:
        proc_load = 0.5
    if proc_load < 1.0:
        mood = "🍷🗿"
    elif proc_load < 2.5:
        mood = "😎"
    else:
        mood = "🔥"
    status_emoji = "🟢"

    text = (
        f"# {status_emoji} {tr(lang, 'status_title')}\n\n"
        f"✦ 彡 巛 〢 ✦ 彡 巛 〢 ✦\n\n"
        f"**{tr(lang, 'status_online')}**\n\n"
        f"- {tr(lang, 'status_uptime')}: `{human_uptime()}`\n"
        f"- {tr(lang, 'status_latency')}: `~{max(1, int(proc_load * 40))} ms`\n"
        f"- {tr(lang, 'status_mode')}: `{mode_label}`\n"
        f"- {tr(lang, 'status_mood')}: `{tr(lang, 'status_mood_value')}`\n\n"
        f"{mood} · v{BOT_VERSION}"
    )
    try:
        await send_formatted(chat_id, text, reply_to=message.message_id)
    except Exception as e:
        logger.warning(f"status send fail: {e}")
        await reply_tg_html(message, f"🟢 {tr(lang, 'status_online')} · {human_uptime()}")


async def handle_toggle_premium(message: telebot.types.Message) -> None:
    if message.from_user is None or message.from_user.id != PREMIUM_ADMIN_ID:
        await reply_tg_html(message, "⛔ Нет доступа.")
        return
    state.premium_functions_enabled = not state.premium_functions_enabled
    label = "включены ✅" if state.premium_functions_enabled else "выключены ❌"
    await reply_tg_html(message, f"Расширенные функции: {label}")


async def handle_pre_checkout(pre_checkout: telebot.types.PreCheckoutQuery) -> None:
    await tg_bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


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
    await reply_tg_html(message, tr(lang, "donate_thanks", stars))


# ============================================================
# TG CONFIG / AVATAR / RECALL / SEARCH / CHART / FMB
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
            config_text("tg", chat_id, user_id),
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
                re.sub(r'<[^>]+>', '', config_text("tg", chat_id, user_id)),
                reply_markup=build_main_config_keyboard("tg", chat_id, user_id),
            )
        except Exception as e2:
            logger.error(f"Config fallback fail: {e2}")


async def tg_handle_avatar(message: telebot.types.Message, chat_id: int, user_id: int) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    raw = await get_avatar_description_tg(message, chat_id, user_id, lang=lang)
    if not raw:
        await reply_tg_html(message, tr(lang, "avatar_fail"))
        return
    segments = clean_extra_text(raw)
    if not segments:
        await reply_tg_html(message, tr(lang, "avatar_fail"))
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
        await reply_tg_html(message, tr(lang, "recall_fail"))
        return
    segments = clean_extra_text(raw)
    if not segments:
        await reply_tg_html(message, tr(lang, "recall_fail"))
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
        await reply_tg_html(message, tr(lang, "search_need_query"))
        return
    status = await tg_bot.send_message(chat_id, tr(lang, "search_starting", query))
    results = await web_search(query, max_results=6)
    try:
        await tg_bot.delete_message(chat_id, status.message_id)
    except Exception:
        pass
    if not results:
        await reply_tg_html(message, tr(lang, "search_nothing"))
        return
    context = format_search_results(results)
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
        full += "\n\n<b>" + tr(lang, "search_source") + ":</b>\n" + "\n".join(sources)
    await send_formatted(chat_id, full, reply_to=message.message_id)


async def tg_handle_chart_request(message: telebot.types.Message, description: str,
                                  chat_id: int, user_id: int,
                                  user_images: list[bytes] | None = None) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    if not description.strip():
        await reply_tg_html(message, tr(lang, "chart_usage"))
        return
    status = await tg_bot.send_message(chat_id, tr(lang, "chart_building"))
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
        m = re.search(r'\{[\s\S]*\}', raw or "")
        if m:
            try:
                spec = json.loads(m.group(0))
            except Exception:
                spec = None
    if not isinstance(spec, dict):
        try:
            await tg_bot.edit_message_text(tr(lang, "chart_error", "invalid JSON"), chat_id, status.message_id)
        except Exception:
            pass
        return
    try:
        img = await render_infographic(spec, user_images=user_images)
    except Exception as e:
        logger.error(f"chart render error: {e}")
        try:
            await tg_bot.edit_message_text(tr(lang, "chart_error", str(e)), chat_id, status.message_id)
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
            caption=spec.get("title") or tr(lang, "chart_built"),
            reply_to_message_id=message.message_id,
        )
    except Exception as e:
        logger.error(f"chart send error: {e}")
        await reply_tg_html(message, tr(lang, "chart_error", str(e)))


# ============================================================
# FEMBOY RATE
# ============================================================
async def tg_handle_femboy_rate(message: telebot.types.Message, chat_id: int, user_id: int,
                                photo_bytes: bytes, caption: str = "") -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    status = await tg_bot.send_message(chat_id, tr(lang, "femboy_analyzing"))
    try:
        include_advice = bool("совет" in caption.lower() or "advice" in caption.lower())
        theme = cfg.get("theme", "dark")
        ai_data = await get_femboy_data(photo_bytes, include_advice, lang=lang)
        if "error" in ai_data:
            await tg_bot.edit_message_text(ai_data['error'], chat_id, status.message_id)
            return
        infographic = await create_femboy_infographic(photo_bytes, ai_data, theme=theme, lang=lang)
        report = (
            f"<b>{tr(lang, 'femboy_title')}</b>\n\n"
            f"{tr(lang, 'femboy_gender')} {ai_data.get('gender', '?')}\n"
            f"{tr(lang, 'femboy_score')} <code>{ai_data.get('fmb', '?')}/10.0</code>\n"
            f"{tr(lang, 'femboy_tier')} <code>{ai_data.get('tier', '?')}</code>\n"
        )
        if ai_data.get("potential"):
            report += f"{tr(lang, 'femboy_potential')} <code>{ai_data['potential']}</code>\n"
        report += f"\n<b>{tr(lang, 'femboy_analysis')}</b>\n{html.escape(ai_data.get('summary', ''))}"
        if include_advice and ai_data.get("advice"):
            report += f"\n\n<b>{tr(lang, 'femboy_advice')}</b>\n{html.escape(ai_data['advice'])}"
        try:
            await tg_bot.send_photo(chat_id, InputFile(infographic),
                                    caption=tr(lang, "femboy_report"))
        except Exception as e:
            logger.error(f"femboy infographic send: {e}")
        for chunk in [report[i:i + 3900] for i in range(0, len(report), 3900)]:
            try:
                await tg_bot.send_message(chat_id, chunk, parse_mode='HTML')
            except Exception:
                await tg_bot.send_message(chat_id, re.sub(r'<[^>]+>', '', chunk))
        await tg_bot.delete_message(chat_id, status.message_id)
    except Exception as e:
        logger.error(f"femboy rate: {e}")
        await reply_tg_html(message, f"🌋 Ошибка: {e}")


async def tg_process_femboy_album(media_group_id: str, chat_id: int, user_id: int) -> None:
    from src.util import battle_photos as bp
    for _ in range(10):
        if media_group_id in bp and len(bp[media_group_id]) >= 2:
            break
        await asyncio.sleep(0.5)
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    if media_group_id not in bp or len(bp[media_group_id]) < 2:
        bp.pop(media_group_id, None)
        await tg_bot.send_message(chat_id, tr(lang, "femboy_battle_need_photos"))
        return
    photos = bp.pop(media_group_id)
    p1, p2 = photos[:2]
    theme = cfg.get("theme", "dark")
    status = await tg_bot.send_message(chat_id, tr(lang, "femboy_battle_waiting"))
    ai_data = await get_femboy_battle_data(p1, p2, lang=lang)
    if "error" in ai_data:
        await tg_bot.edit_message_text(ai_data['error'], chat_id, status.message_id)
        return
    battle_img = await create_femboy_battle_infographic(p1, p2, ai_data, theme=theme, lang=lang)
    winner_num = str(ai_data.get("winner", "1"))
    winner_label = tr(lang, "femboy_battle_first") if winner_num == "1" else tr(lang, "femboy_battle_second")
    report_text = (
        f"<b>{tr(lang, 'femboy_battle_title')}</b>\n\n"
        f"{tr(lang, 'femboy_battle_winner')} <b>{winner_label}</b>\n"
        f"{tr(lang, 'femboy_battle_reason')} {html.escape(ai_data.get('reason', ''))}\n\n"
        f"{tr(lang, 'femboy_battle_photo1')} FMB {ai_data.get('photo1', {}).get('fmb', '?')} | "
        f"Tier {html.escape(str(ai_data.get('photo1', {}).get('tier', '?')))}\n"
        f"{tr(lang, 'femboy_battle_photo2')} FMB {ai_data.get('photo2', {}).get('fmb', '?')} | "
        f"Tier {html.escape(str(ai_data.get('photo2', {}).get('tier', '?')))}\n"
    )
    try:
        await tg_bot.send_photo(chat_id, InputFile(battle_img), caption=tr(lang, "femboy_battle_caption"))
    except Exception as e:
        logger.error(f"femboy battle infra: {e}")
    try:
        await tg_bot.send_message(chat_id, report_text, parse_mode='HTML')
    except Exception:
        await tg_bot.send_message(chat_id, re.sub(r'<[^>]+>', '', report_text))
    await tg_bot.delete_message(chat_id, status.message_id)


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


# ============================================================
# STREAMING
# ============================================================
async def stream_text_via_drafts(chat_id: int, text: str, is_private: bool = True) -> bool:
    if not state.premium_functions_enabled:
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
async def send_tg_ai_response(message: telebot.types.Message, chat_id: int, user_id: int,
                              answer_raw: str, user_text: str | None = None,
                              user_images: list[bytes] | None = None) -> None:
    cfg = get_user_config("tg", chat_id, user_id)
    lang = cfg.get("language", "ru")
    separate_enabled = cfg.get("separate_enabled", True)
    streaming = cfg.get("streaming_enabled", False) and state.premium_functions_enabled

    if streaming and separate_enabled:
        streaming = False

    # ---- !search ----
    if cfg.get("web_search_enabled", True):
        query, _ = extract_search_marker(answer_raw or "")
        if query:
            results = await web_search(query, max_results=6)
            if results:
                context = format_search_results(results)
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
                answer_raw = tr(lang, "search_nothing")

    # ---- !recall_media: подтягиваем последнее медиа и перезапускаем AI с ним ----
    if UTILITY_PATTERNS["recall_media"].search(answer_raw or ""):
        orig = (user_text or (message.text or message.caption or "")).strip()
        media_bytes: bytes | None = None
        media_kind: str = ""
        try:
            media_bytes, media_kind = await _media().fetch_last_media_tg(chat_id)
        except Exception as e:
            logger.warning(f"recall fetch: {e}")
            media_bytes, media_kind = None, ""

        if media_bytes:
            kind_label = {"photo": "фото", "video": "видео", "animation": "гифку"}.get(media_kind, "медиа")
            follow_prompt = (
                f"Пользователь написал: {orig or 'покажи последнее медиа'}\n\n"
                f"Вот последнее медиа в чате — это {kind_label}. Опиши, что на нём, и ответь на запрос "
                f"пользователя естественно, как ты обычно общаешься (маленькие буквы, без вычурной "
                f"пунктуации). Можешь разбить на 1-2 сообщения через !separate, если хочется. "
                f"НЕ используй маркеры !search, !chart, !recall_media, !avatar, !sticker, !gif."
            )
            new_answer = await ask_ai_async(
                prompt=follow_prompt,
                image_bytes=media_bytes, image_mime="image/jpeg",
                chat_id=chat_id, user_id=user_id, platform="tg",
            )
            if new_answer and new_answer.strip():
                logger.info(f"✅ recall_media: kind={media_kind}, bytes={len(media_bytes)}")
                answer_raw = new_answer
            else:
                logger.warning("recall_media: AI вернул пусто на медиа")
                answer_raw = _strip_recall_marker(answer_raw) + "\n" + tr(lang, "recall_fail")
        else:
            logger.info("recall_media: медиа в истории не найдено")
            answer_raw = _strip_recall_marker(answer_raw) + "\n" + tr(lang, "recall_fail")

    # ---- !chart ----
    if state.premium_functions_enabled:
        chart_spec, remaining = extract_chart_marker(answer_raw or "")
        if chart_spec:
            user_asked_chart = user_wants_chart(user_text or message.text or message.caption or "")
            if user_asked_chart:
                try:
                    img = await render_infographic(chart_spec, user_images=user_images)
                    try:
                        await tg_bot.send_photo(
                            chat_id, InputFile(img, file_name="infographic.png"),
                            caption=chart_spec.get("title") or tr(lang, "chart_built"),
                            reply_to_message_id=message.message_id,
                        )
                    except Exception as e:
                        logger.error(f"chart send: {e}")
                except Exception as e:
                    logger.error(f"chart render: {e}")
                    answer_raw = remaining + "\n" + tr(lang, "chart_error", str(e))
                    chart_spec = None
            if chart_spec is not None or not user_asked_chart:
                answer_raw = remaining

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
        # Этот маркер уже обработан выше — просто вырезаем его из списка.
        markers.remove("recall_media")

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
                await stream_text_via_drafts(message.chat.id, seg, is_private=True)
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
# OLD MESSAGE REPLY (TG) — в стиле обычного чата
# ============================================================
async def maybe_reply_to_old_message_tg(message: telebot.types.Message, chat_id: int, user_id: int) -> None:
    # Небольшая пауза, чтобы «внезапный» ответ не прилетал мгновенно после основного.
    try:
        await asyncio.sleep(3)
    except asyncio.CancelledError:
        return
    chat_key = f"tg_{chat_id}"
    now = time.time()
    if now - last_old_reply.get(chat_key, 0) < 600:
        return
    if random.random() > 0.12:
        return
    mem = list(get_chat_memory(chat_key))
    current_msg_id = message.message_id
    # Исключаем ТЕКУЩЕЕ сообщение из кандидатов — иначе бот отвечает на ту же просьбу повторно.
    candidates = [
        e for e in mem[:-2]
        if e.get("type") == "user"
        and e.get("text")
        and e.get("message_id") != current_msg_id
    ]
    if not candidates:
        return
    old = random.choice(candidates)
    try:
        comment = await ask_ai_async(
            prompt=(
                f"Сейчас идёт живая переписка. Ты краем глаза заметил старое сообщение от "
                f"{old.get('display','?')}: \"{old.get('text','')}\". Хочешь коротко и по-пацански "
                f"прокомментировать его прямо сейчас, не прерывая текущий вайб? Если да — напиши одно "
                f"короткое сообщение в том же стиле, в котором ты общаешься со всеми: маленькие буквы, "
                f"без лишней пунктуации, естественно, эмодзи только если очень хочется. "
                f"Если не хочешь — ответь ровно 'НЕТ'."
            ),
            system_instruction_override=(
                "Ты Кульш. Если комментируешь — пиши как в обычном чате с кентами: "
                "маленькими буквами, без вычурной пунктуации, живо. Или ответь 'НЕТ'."
            ),
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