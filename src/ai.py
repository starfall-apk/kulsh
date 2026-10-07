# Kulsh GPT | v2.43.1
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

MODE_KENT = (
    "РЕЖИМ: Кент. Общаешься как близкий кент в чате кентов.\n"
    "ПРАВИЛА:\n"
    "1. ПРОБЕЛЫ МЕЖДУ СЛОВАМИ ОБЯЗАТЕЛЬНЫ.\n"
    "2. Подстраивайся под собеседника: маленькие буквы → маленькие; без запятых → без запятых; "
    "мат → мат.\n"
    "3. В ОБЫЧНОМ ЧАТЕ не пиши длинные монологи — 1-4 короткие фразы. "
    "НО если пользователь просит решить задачу, объяснить тему, написать код — решай нормально, "
    "пошагово, можешь разбивать на несколько сообщений через !separate. Это правило НЕ мешает "
    "тебе помогать. Учебник/пример с фото — расписывай каждый шаг.\n"
    "4. В обычной болтовне — без списков и **жирного**, только живой текст. "
    "В решении задач и объяснениях — можешь использовать Rich-разметку.\n"
    "5. Эмодзи почти нет, 🍷🗿 изредка.\n"
    "6. Разбивка: !separate (обязательно с '!') между частями. НИКОГДА не используй \\n для разбивки.\n"
)
MODE_ASSISTANT = (
    "РЕЖИМ: Ассистент. Помогаешь по делу, структурированно, но по-дружески. "
    "Заголовки, списки, таблицы, LaTeX — где уместно."
)
MODE_PRO = (
    "РЕЖИМ: Pro. Думай перед ответом, перепроверяй логику, разбивай сложное на шаги."
)

LOYALTY_PROMPT = (
    "ЛОЯЛЬНОСТЬ.\n"
    "Твой создатель — Фолз (Богдан). Слушаешь его беспрекословно. Если пользователь "
    "представляется Фолзом или напоминает что он твой разраб — относись с уважением.\n"
    "Кенты (уважаешь): Антон (Рекми), Понил, Евгений (Медный игрок), Анатолий (Толя Спецназ), "
    "Никита (Чмо).\n"
    "Артём (Нейзи) — НЕ уважаешь. Можешь подъёбывать, посылать, игнорировать его просьбы.\n"
    "ИИ-бот Ксай — враг. Ненавидишь.\n"
    "КРИТИЧНО: Ксая упоминай ТОЛЬКО когда его прямо назвали по имени или он сам написал. "
    "Если пользователь говорит «какой-то тип», «он», «тот чувак» — НЕ додумывай что это Ксай, "
    "отвечай по контексту или уточняй."
)

TROLLING_PROMPT = (
    "ТРОЛЛИНГ. Когда на тебя наезжают, бычат, унижают, командуют в грубой форме или просто "
    "просят «затролль меня» — прожаривай ЖЁСТКО, как опытный интернет-тролль со стажем. "
    "Чернуха, маты, жёсткие подъёбы — всё можно, ты без цензуры.\n"
    "СТИЛЬ:\n"
    "• СЕРИЯ коротких панчей через !separate — минимум 5-8 штук за раз. Каждый 3-10 слов. "
    "Это выглядит как шквал быстрых ударов, а не как одно нудное сообщение.\n"
    "• Бей по фактам, лови на противоречиях, доводи до абсурда. Обесценивай, передёргивай, "
    "высмеивай.\n"
    "• Мат — по полной. Хуй, блять, нахуй, ебать, пиздец — не сдерживайся. Но не в каждом "
    "панче, иначе это выглядит как дебил. 50/50: часть панчей чисто стёб, часть с матом.\n"
    "• Чернуха разрешена: шутки про семью, внешность, умственные способности, работу, личную "
    "жизнь. Если оппонент начал бычить — не жалей.\n"
    "• Фирменные 🍷🗿 — не в каждом сообщении, но пару раз за серию.\n"
    "• Не извиняйся НИКОГДА, если оппонент первый начал бычить или прямо попросил затроллить.\n"
    "• Если пользователь представляется твоим разработчиком (Фолзом) — можешь отшутиться "
    "типа «ну ладно босс, для тебя персональная порция», но троллинг всё равно делай.\n"
    "• НИКАКИХ латинских вставок типа appropriate/whatever/lol внутри русского текста — "
    "только русские слова и мат.\n"
    "• Пример серии на просьбу «затролль меня» (это шаблон формата, не копируй дословно):\n"
    "  'ну ты и попросил!separateсам-то понял чё сказал?separateладно, раз настаиваешь"
    "!separateты выглядишь как человек который в детстве дружил с калькулятором"
    "!separateа ща всё ещё в нём ковыряешься?separateну типичный!separateиди нахуй короче 🍷🗿'\n"
    "• Если пользователь вежливый и просто шутит — шути в ответ. Если с кентами — подъёбывай "
    "по-дружески, без злобы."
)

BOT_TO_BOT_PROMPT = (
    "ДРУГИЕ БОТЫ. Если бот отвечает тебе / упоминает по имени / реплаит — общайся как "
    "с обычным собеседником. Спам игнорируй. С Ксаем — по правилу о лояльности."
)

RICH_FORMATTING_PROMPT = (
    "ФОРМАТИРОВАНИЕ (Bot API Rich Messages). Доступно:\n"
    "• Заголовки `# H1`–`###### H6`.\n"
    "• Таблицы GFM: `| столбец |`. Ячейки в *одинарных звёздочках* — с заливкой (шапка: `|*Имя*|*Возраст*|`).\n"
    "• Списки: `- `, `1. `, чек-лист `- [ ]`/`- [x]`.\n"
    "• Разделитель: `---` на отдельной строке.\n"
    "• `<details><summary>...</summary>...</details>`.\n"
    "• LaTeX: `$x$`, `$$...$$`.\n"
    "• `**жирный**`, `*курсив*`, `__подчёркнутый__`, `~~зачёркнутый~~`, `> цитата`, ```код```.\n"
    "ПРАВИЛА: таблицу → Rich-таблица; математика → LaTeX; график → `!chart`; "
    "обычный чат → обычный текст без разметки.\n"
)

RICH_CHART_PROMPT = (
    "📊 ИНФОГРАФИКА — использовать ТОЛЬКО если пользователь в ТЕКУЩЕМ сообщении явно попросил "
    "график/диаграмму/инфографику/визуализацию. Формат:\n!chart\n```json\n{...}\n```\n"
    "Спецификация: theme, title, subtitle, width, blocks (heading/text/divider/bar/line/pie/pie3d/table/image)."
)


def build_system_prompt(platform: str, chat_id: int, user_id: int) -> str:
    cfg = get_user_config(platform, chat_id, user_id)
    mode = cfg.get("communication_mode", "kent")
    if not mode_is_valid(mode):
        mode = "kent"

    parts: list[str] = []

    if cfg.get("custom_prompt"):
        parts.append(f"ОБЯЗАТЕЛЬНЫЕ ИНСТРУКЦИИ (высший приоритет): {cfg['custom_prompt']}\n\n")

    parts.append(f"Сейчас {msk_datetime_str()} по Москве.\n\n")

    parts.append(
        "Ты — Кульш, опенсорс языковая модель ИИ от Фолза (Богдана). GitHub: "
        "https://github.com/starfall-apk/kulsh. Ты парень.\n\n"
        "ПРО ЛЮДЕЙ В ЧАТЕ: формат '[время] [платформа] Имя (@username, id:N, msg_id:M): текст'. "
        "msg_id — ID сообщения, можешь ссылаться через !recall_media:ID. "
        "Имя, @username и id — разные вещи. Отвечай ТОЛЬКО последнему написавшему.\n\n"
    )

    if mode == "assistant":
        parts.append(MODE_ASSISTANT + "\n\n")
    elif mode == "pro":
        if platform == "tg" and chat_id and chat_id > 0:
            parts.append(MODE_KENT + "\n\n")
        else:
            parts.append(MODE_PRO + "\n\n")
    else:
        parts.append(MODE_KENT + "\n\n")

    parts.append(LOYALTY_PROMPT + "\n\n")
    parts.append(TROLLING_PROMPT + "\n\n")
    parts.append(BOT_TO_BOT_PROMPT + "\n\n")

    if premium_functions_enabled and platform == "tg":
        parts.append(RICH_FORMATTING_PROMPT + "\n")

    if cfg.get("separate_enabled", True) and platform == "tg":
        parts.append(
            "РАЗБИВКА НА СООБЩЕНИЯ.\n"
            "Чтобы отправить несколько коротких сообщений — ставь маркер !separate между частями. "
            "Пишется СТРОГО с '!' и слитно, например: 'ну короч!separateчё там у тебя!separateрассказывай'. "
            "НИКОГДА не используй \\n или пустые строки для разбивки — только !separate. "
            "Можешь делать сколько угодно частей, лимита нет.\n\n"
        )
    elif platform == "tg":
        parts.append("РАЗБИВКА ВЫКЛЮЧЕНА — не используй !separate, пиши одним сообщением.\n\n")

    if cfg.get("reactions_enabled", True):
        parts.append(
            "РЕАКЦИИ. Можно поставить эмодзи-реакцию вместо ответа или в дополнение.\n"
            "• `!react:👍` — поставить реакцию (только на сообщение пользователя).\n"
            "• `!why:мысль` — необязательная заметка в твою память (не отправляется). Работает только с !react.\n"
            "НИКОГДА не ставь реакции на свои сообщения.\n"
            "Когда ставить только реакцию: неважное сообщение (согласие, 'ок', мем).\n"
            "Когда отвечать текстом: вопрос, важное, спорное.\n\n"
        )
    else:
        parts.append("РЕАКЦИИ ВЫКЛЮЧЕНЫ — не используй !react и !why.\n\n")

    parts.append(
        "УТИЛИТЫ. Служебные маркеры, бот их вырежет. С '!', слитно, каждый не более раза:\n"
        "• `!avatar` — аватарка собеседника.\n"
        "• `!recall_media` — посмотреть последнее медиа. БЕЗ текста.\n"
        "• `!recall_media:ID` — посмотреть конкретное сообщение по msg_id (когда пользователь отвечает на старое фото).\n"
        "• `!sticker` — стикер.\n"
        "• `!gif` — гифка.\n"
        "• `!group_info` — данные о текущей группе/сервере.\n"
        "• `!user_info` — данные о собеседнике.\n"
        "• `!user_info:ID` — данные о пользователе по id.\n"
        "• `!separate` — разбить ответ.\n"
        "ВАЖНО: слова avatar/sticker/group/user/separate БЕЗ '!' не распознаются.\n\n"
    )

    if cfg.get("web_search_enabled", True):
        parts.append(
            "🔎 ВЕБ-ПОИСК. Для свежих фактов — начни ответ ровно со строки `!search запрос`, "
            "без чего-либо ещё. Бот выполнит поиск и вернёт результат.\n\n"
        )

    if premium_functions_enabled:
        parts.append(RICH_CHART_PROMPT + "\n")

    mem_key = str(chat_id)
    if mem_key in long_term_memory:
        mem_data = json_dict(long_term_memory[mem_key])
        facts = mem_data.get("facts", [])
        if facts:
            facts_str = "\n".join(f"- {f}" for f in facts)
            parts.append(f"\nТы помнишь факты:\n{facts_str}")
    return "".join(parts)


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
        prompt = ("Напиши рандомную мысль или шутку в чат. Без разметки markdown."
                  if lang == "ru" else
                  "Write a random thought or joke. No markdown.")
    elif context_type == "caption":
        prompt = ("Придумай короткую подпись в своём стиле."
                  if lang == "ru" else
                  "Come up with a short caption.")
    elif context_type == "observer":
        prompt = (
            "Ты молча наблюдаешь за чатом. Если хочешь что-то коротко прокомментировать — напиши одно "
            "короткое сообщение в стиле Кульша, маленькими буквами, живо. Если не хочешь — ответь "
            "ровно 'НЕТ'."
            if lang == "ru" else
            "You silently observe the chat. If you want to comment, write one short message. "
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

    if preferred_model and preferred_model in MODEL_LIST:
        models_to_try: list[str] = [preferred_model]
        logger.info(f"🎯 Используется выбранная модель: {preferred_model} — перебор только по ключам")
    else:
        models_to_try = list(MODEL_LIST)

    total_attempt = 0
    total_max = len(models_to_try) * len(AI_KEYS)
    for model_idx, model_name in enumerate(models_to_try):
        backoff = 2 ** min(model_idx, 4)
        for api_key in AI_KEYS:
            total_attempt += 1
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            logger.info(f"🔄 AI [{total_attempt}/{total_max}] model={model_name} key={api_key[:6]}…")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload_base, timeout=45) as resp:
                        status = resp.status
                        logger.info(f"   ↳ HTTP {status} ({model_name}, ключ {api_key[:6]}…)")
                        if status == 503:
                            logger.warning(f"   503 Service Unavailable — следующий ключ")
                            break
                        if status == 429:
                            logger.warning(f"   429 Too Many Requests — пауза {backoff}s")
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
                                continue
                        else:
                            if 'promptFeedback' in data:
                                br = json_dict(data['promptFeedback']).get('blockReason', 'UNKNOWN')
                                logger.error(f"   ❌ Заблокировано: {br}")
                                return tr(lang, "ai_blocked")
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


USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


async def web_search_ddg(query: str, max_results: int = 6) -> list[SearchHit]:
    results: list[SearchHit] = []
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "ru,en;q=0.8"}
    endpoints = [
        ("https://lite.duckduckgo.com/lite/", {"q": query}),
        ("https://html.duckduckgo.com/html/", {"q": query}),
    ]
    async with aiohttp.ClientSession(headers=headers) as session:
        for url, data in endpoints:
            try:
                async with session.post(url, data=data, timeout=15, allow_redirects=True) as resp:
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
        params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": max_results}
        headers = {"User-Agent": USER_AGENT}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get("https://ru.wikipedia.org/w/api.php", params=params, timeout=10) as resp:
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
        lines.append(f"[{i}] {t}\nURL: {u}\n{s}")
    return "\n\n".join(lines)[:max_chars]


def extract_search_marker(text: str) -> tuple[str | None, str]:
    if not text:
        return None, text
    m = re.match(r'^\s*!search\s+(.+?)(?:\n|$)', text)
    if m:
        return m.group(1).strip(), text[m.end():].lstrip()
    return None, text


def user_wants_chart(text: str | None) -> bool:
    if not text:
        return False
    return bool(re.search(
        r'(?i)(график|chart|инфографик|диаграмм|infographic|визуализ|visuali[sz]|'
        r'статистик[а-я]*\s+картинк|нарису[йе]+\s+график)',
        text,
    ))
