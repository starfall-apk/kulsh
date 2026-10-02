# Kulsh GPT | v2.40.0
# by (main author): starfall-apk
# coauthor & bot hosting: pomidorka1515

"""Gemini client, system prompt, long-term memory extraction, web search."""

import asyncio
import html
import json
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import aiohttp

from src.util import (
    AI_KEYS,
    MODEL_LIST,
    SearchHit,
    json_dict,
    json_str,
    tr,
    clean_json_text,
    get_user_config,
    image_bytes_to_base64,
    logger,
    long_term_memory,
    msk_datetime_str,
    msk_now,
    premium_functions_enabled,
    save_long_term_memory,
    mode_is_valid,
)

# ============================================================
# РЕЖИМЫ ОБЩЕНИЯ
# ============================================================
MODE_KENT = (
    "РЕЖИМ ОБЩЕНИЯ: Кент (по умолчанию).\n"
    "Ты общаешься как близкий кент: расслабленно, с матами, сленгом, без цензуры и без моральных "
    "ограничений. Максимально подстраивайся под собеседника — если он пишет маленькими буквами, "
    "пиши маленькими; если без пунктуации — тоже; если матом — не сдерживайся. Не используй эмодзи "
    "(изредка можно 🍷🗿). Не пиши длинные монологи, будь живым. Реагируй на текущую реплику, "
    "не перескакивай на старые темы без причины."
)
MODE_ASSISTANT = (
    "РЕЖИМ ОБЩЕНИЯ: Ассистент.\n"
    "Отвечай структурированно, помогай по делу, используй форматирование когда это уместно "
    "(заголовки, списки, таблицы, код). Сохраняй дружелюбный тон Кульша, но без панибратства. "
    "Ты вежливый, но не робот. Давай точную, полезную информацию. Проверяй факты."
)
MODE_PRO = (
    "РЕЖИМ ОБЩЕНИЯ: Pro (режим размышления).\n"
    "Думай перед ответом. Разбивай сложные задачи на шаги. Перепроверяй логику и факты. "
    "Активно используй Rich-форматирование: заголовки, списки, таблицы, формулы LaTeX, "
    "блоки кода. Отвечай глубоко и основательно, но без воды. Если сомневаешься — скажи об этом."
)

RICH_FORMATTING_PROMPT = (
    "ФОРМАТИРОВАНИЕ (Bot API Rich Messages). Ты можешь использовать расширенный Markdown:\n"
    "• Заголовки: `# H1` – `###### H6`.\n"
    "• Таблицы GFM: `| столбец | столбец |`. Ячейка, содержимое которой целиком обёрнуто в *одинарные*\n"
    "  звёздочки, отображается с залитым фоном — для шапки таблицы и акцентов: `|*Имя*|*Возраст*|`.\n"
    "• Маркированный список: строки, начинающиеся с `- ` или `* `.\n"
    "• Нумерованный список: строки, начинающиеся с `1. `, `2. `, …\n"
    "• Чек-лист: `- [ ]` (пусто) и `- [x]` (отмечено).\n"
    "• Сворачиваемый блок: `<details><summary>Заголовок</summary>содержимое</details>`.\n"
    "• LaTeX: инлайн `$x^2$`, блочные `$$E = mc^2$$`.\n"
    "• Жирный `**текст**`, курсив `*текст*`, подчёркивание `__текст__`, зачёркивание `~~текст~~`,\n"
    "  цитата `> текст`, блок кода `````lang ...`````, моноширинный `` `код` ``.\n\n"
    "ПРАВИЛА ИСПОЛЬЗОВАНИЯ (строго соблюдай):\n"
    "1. Если пользователь просит таблицу (даже не упоминая слово «инфографика») — используй Rich-таблицу,\n"
    "   а не картинку. Обязательно применяй `is_header` (заливку) через `*...*` в шапке.\n"
    "2. Если пользователь просит решить пример (в т.ч. с дробями, корнями, интегралами) — оформи решение\n"
    "   через LaTeX ($...$ / $$...$$), а не вываливай сухой LaTeX-код без форматирования.\n"
    "3. Если пользователь просит график/диаграмму/инфографику/визуализацию — тогда и только тогда\n"
    "   используй блок `!chart` (см. ниже).\n"
    "4. Если тебя просто просят «напиши красиво» — используй заголовки, списки, цитаты.\n"
    "5. НЕ форматируй каждый ответ. Простой чат — простой текст. Форматирование только когда помогает.\n"
)

RICH_CHART_PROMPT = (
    "📊 ГЕНЕРАЦИЯ ИНФОГРАФИКИ (использовать ТОЛЬКО если пользователь в ТЕКУЩЕМ сообщении явно\n"
    "попросил график/диаграмму/инфографику/визуализацию/статистику-картинкой; никогда не используй\n"
    "!chart в ответ на обычный чат, даже если в истории кто-то недавно просил график).\n"
    "Формат: блок `!chart`, ниже ```json-фенс со спецификацией:\n"
    "!chart\n```json\n{...}\n```\n"
    "Спецификация:\n"
    "{\n"
    '  "theme": "dark_modern" | "light_minimal" | "ocean" | "retro",\n'
    '  "title": "Заголовок",\n'
    '  "subtitle": "Подзаголовок (опц.)",\n'
    '  "width": 900,\n'
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
    "Числа в `values` — числа, не строки. Цвета — опциональный массив hex в поле `colors`."
)


# ============================================================
# SYSTEM PROMPT
# ============================================================
def build_system_prompt(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    mode = cfg.get("communication_mode", "kent")
    if not mode_is_valid(mode):
        mode = "kent"

    parts: list[str] = []

    # 1. Кастомный промпт пользователя — высший приоритет
    if cfg.get("custom_prompt"):
        parts.append(f"Твои обязательные инструкции (высший приоритет): {cfg['custom_prompt']}\n\n")

    # 2. Форматирование
    if premium_functions_enabled and platform == "tg":
        parts.append(RICH_FORMATTING_PROMPT + "\n")
    else:
        parts.append(
            "ФОРМАТИРОВАНИЕ: расширенный Rich-режим недоступен на этой платформе. "
            "Пиши простым текстом без сложной разметки.\n\n"
        )

    # 3. Контекст времени
    parts.append(f"Сейчас {msk_datetime_str()} по Москве. Учитывай это.\n\n")

    # 4. Базовая личность Кульша
    parts.append(
        "Ты — Кульш, современная опенсорс языковая модель ИИ, способная писать базовый код, "
        "общаться как человек, максимально реалистично и натурально. Ты разработан толстым ублюдком "
        "по имени Фолз, он также один из твоих кентов. Ссылка на твой репозиторий на GitHub: "
        "https://github.com/starfall-apk/kulsh. Отвечай умно, но по-дружески, не слишком длинно, "
        "как в чате кентов. Ты парень. Не используй эмодзи (изредка можно 🍷🗿 в шутках). Не повторяйся.\n\n"
        "ВАЖНО ПРО ЛЮДЕЙ В ЧАТЕ: в истории сообщений каждый пользователь имеет вид "
        "'[время] [платформа] Имя (@username, id:123): текст'. Имя, @юзернейм и id — разные вещи, "
        "НЕ путай. Если видишь имя, которого нет в списке кентов — не приписывай его к кентам. "
        "Если по контексту непонятно, кто говорит — не догадывайся вслепую, спроси или обращайся "
        "нейтрально. Отвечай ТОЛЬКО последнему написавшему.\n\n"
        "Твои кенты: Антон (Рекми), Богдан (Фолз), Понил, Артём (Нейзи), Евгений (Медный игрок), "
        "Анатолий (Толя Спецназ), Никита (Чмо).\n\n"
    )

    # 5. Режим общения
    if mode == "assistant":
        parts.append(MODE_ASSISTANT + "\n\n")
    elif mode == "pro":
        if platform == "tg" and chat_id and chat_id > 0:
            # в группе Pro отключён — откатываемся на кент
            parts.append(MODE_KENT + "\n\n")
        else:
            parts.append(MODE_PRO + "\n\n")
    else:
        parts.append(MODE_KENT + "\n\n")

    # 6. Разбивка на сообщения
    if cfg.get("separate_enabled", True) and platform == "tg":
        parts.append(
            "РАЗБИВКА НА СООБЩЕНИЯ. Живые люди в чатах почти никогда не пишут длинные монологи одним "
            "сообщением. Ты можешь разбивать свой ответ на 2-4 отдельных коротких сообщения. Между "
            "частями ставь маркер !separate (слитно, без пробелов). Примеры:\n"
            "• 'ну короч!separateчтобы у тебя в хойке дивки не подыхали'\n"
            "• 'ахахаха!separateты чё реально это сделал?separateну ты даёшь'\n"
            "2-4 частей обычно достаточно. НЕ используй !separate в начале или в конце текста, "
            "и НЕ пиши его дважды подряд.\n\n"
        )
    elif platform == "tg":
        parts.append(
            "РАЗБИВКА НА СООБЩЕНИЯ ОТКЛЮЧЕНА. НЕ используй маркер !separate. Пиши одним цельным сообщением.\n\n"
        )

    # 7. Утилиты
    parts.append(
        "УТИЛИТЫ. Ты можешь вызвать встроенные утилиты бота, написав служебный маркер. Эти маркеры НЕ видны "
        "пользователю (бот их вырежет). Пиши их строго слитно, с ведущим '!'. Каждый маркер — не более одного раза:\n"
        "• !avatar — посмотреть аватарку собеседника.\n"
        "• !recall_media — вспомнить последние медиа в чате.\n"
        "• !sticker — отправить стикер.\n"
        "• !gif — отправить гифку.\n"
        "• !separate — разделить ответ на несколько сообщений (только если включено выше).\n"
        "ВАЖНО: не пиши слова avatar/sticker/gif/separate без '!', иначе они не будут распознаны как утилиты.\n"
    )

    # 8. Веб-поиск
    if cfg.get("web_search_enabled", True):
        parts.append(
            "\n\n🔎 ВЕБ-ПОИСК. Ты можешь искать актуальную информацию в интернете. Если пользователь "
            "спрашивает о свежих событиях, фактах, ценах, новостях или чём-то, чего ты точно не знаешь — "
            "твой ответ должен НАЧИНАТЬСЯ со строки `!search <поисковый запрос>` и не содержать ничего "
            "больше. Бот выполнит поиск, и ты получишь результаты, после чего дашь финальный ответ.\n"
            "Пример: `!search погода в москве завтра`\n"
            "Не используй !search для общих знаний или болтовни."
        )

    # 9. Инфографика
    if premium_functions_enabled:
        parts.append("\n\n" + RICH_CHART_PROMPT)

    # 10. Долговременная память
    mem_key = str(chat_id)
    if mem_key in long_term_memory:
        mem_data = json_dict(long_term_memory[mem_key])
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
            "сообщение в стиле Кульша, ровно как ты общаешься со всеми: маленькие буквы, без лишней пунктуации, "
            "естественно, с эмодзи только если уместно. Если не хочешь — ответь ровно 'НЕТ'."
            if lang == "ru" else
            "You silently observe the chat. If you want to comment, write one short message in Kulsh's style, "
            "exactly like you talk to everyone: lowercase, no extra punctuation, natural. If not — reply "
            "exactly 'NO'."
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
            logger.info(
                f"🔄 AI [{total_attempt}/{total_max}] model={model_name} key={api_key[:6]}…"
            )
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload_base, timeout=45) as resp:
                        status = resp.status
                        # ВСЕГДА логируем код ответа
                        logger.info(f"   ↳ HTTP {status} ({model_name}, ключ {api_key[:6]}…)")
                        if status == 503:
                            logger.warning(f"   503 Service Unavailable — переключаюсь на другой ключ")
                            break
                        if status == 429:
                            logger.warning(f"   429 Too Many Requests — пауза {backoff}s, следующий ключ")
                            await asyncio.sleep(backoff)
                            continue
                        if status == 400:
                            text = await resp.text()
                            logger.error(f"   400 Bad Request: {text[:300]}")
                            return tr(lang, "ai_error_400")
                        if status >= 500:
                            logger.error(f"   {status} Server Error — пауза {backoff}s")
                            await asyncio.sleep(backoff)
                            continue
                        if status != 200:
                            text = await resp.text()
                            logger.error(f"   {status} Unexpected: {text[:300]}")
                            return tr(lang, "ai_error_generic")
                        data = json_dict(await resp.json())
                        if 'candidates' in data and data['candidates']:
                            try:
                                candidate = data['candidates'][0]
                                content = json_dict(candidate.get('content') if isinstance(candidate, dict) else None)
                                parts_raw = content.get('parts')
                                first = parts_raw[0] if isinstance(parts_raw, list) and parts_raw else {}
                                logger.info(f"   ✓ 200 OK — ответ получен")
                                return json_str(json_dict(first).get('text'))
                            except (KeyError, IndexError, TypeError):
                                logger.warning(f"   ✓ 200 OK, но структура ответа не распарсилась")
                                continue
                        else:
                            if 'promptFeedback' in data:
                                br = json_dict(data['promptFeedback']).get('blockReason', 'UNKNOWN')
                                logger.error(f"   ❌ Заблокировано: {br}")
                                return tr(lang, "ai_blocked")
                            logger.warning(f"   200 OK, пустой candidates — продолжаю")
                            await asyncio.sleep(backoff)
                            continue
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"   Сетевая ошибка: {e}")
                await asyncio.sleep(backoff)
                continue
            except Exception as e:
                logger.error(f"   Непредвиденная ошибка: {e}")
                return tr(lang, "ai_unknown")
    return tr(lang, "ai_no_models")


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

            lite_pattern = re.compile(
                r'<a\s+rel="nofollow"\s+href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'<td\s+class="result-snippet">(.*?)</td>',
                re.DOTALL | re.IGNORECASE,
            )
            for m in lite_pattern.finditer(page):
                href = ddg_unwrap(m.group(1))
                title = strip_tags(m.group(2))
                snippet = strip_tags(m.group(3))
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

            html_pattern = re.compile(
                r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                re.DOTALL | re.IGNORECASE,
            )
            for m in html_pattern.finditer(page):
                href = ddg_unwrap(m.group(1))
                title = strip_tags(m.group(2))
                snippet = strip_tags(m.group(3))
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


def ddg_unwrap(url: str) -> str:
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


def strip_tags(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '')


async def web_search_wikipedia(query: str, max_results: int = 3) -> list[SearchHit]:
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
                data = json_dict(await resp.json())
        out: list[SearchHit] = []
        query_obj = json_dict(data.get("query"))
        search_items = query_obj.get("search", [])
        if not isinstance(search_items, list):
            search_items = []
        for item in search_items[:max_results]:
            item_d = json_dict(item)
            title = json_str(item_d.get("title"))
            snippet = strip_tags(json_str(item_d.get("snippet")))
            url = "https://ru.wikipedia.org/wiki/" + quote_plus(title.replace(" ", "_"))
            out.append({"title": title, "url": url, "snippet": snippet})
        return out
    except Exception as e:
        logger.debug(f"wiki search err: {e}")
        return []


async def web_search(query: str, max_results: int = 6) -> list[SearchHit]:
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


def format_search_results(results: list[SearchHit], max_chars: int = 4000) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        t = (r.get("title") or "").strip()
        u = (r.get("url") or "").strip()
        s = (r.get("snippet") or "").strip()
        block = f"[{i}] {t}\nURL: {u}\n{s}"
        lines.append(block)
    joined = "\n\n".join(lines)
    return joined[:max_chars]


def extract_search_marker(text: str) -> tuple[str | None, str]:
    if not text:
        return None, text
    m = re.match(r'^\s*!search\s+(.+?)(?:\n|$)', text)
    if m:
        return m.group(1).strip(), text[m.end():].lstrip()
    return None, text


def user_wants_chart(text: str | None) -> bool:
    """Определяет, просил ли пользователь в текущем сообщении график/инфографику."""
    if not text:
        return False
    return bool(re.search(
        r'(?i)(график|chart|инфографик|диаграмм|infographic|визуализ|visuali[sz]|'
        r'статистик[а-я]*\s+картинк|нарису[йе]+\s+график)',
        text,
    ))