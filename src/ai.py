# Kulsh GPT | v2.39.0
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
)

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
                            return tr(lang, "ai_error_400")
                        if status >= 500:
                            await asyncio.sleep(backoff)
                            continue
                        if status != 200:
                            text = await resp.text()
                            logger.error(f"{status}: {text[:300]}")
                            return tr(lang, "ai_error_generic")
                        data = json_dict(await resp.json())
                        if 'candidates' in data and data['candidates']:
                            try:
                                candidate = data['candidates'][0]
                                content = json_dict(candidate.get('content') if isinstance(candidate, dict) else None)
                                parts_raw = content.get('parts')
                                first = parts_raw[0] if isinstance(parts_raw, list) and parts_raw else {}
                                return json_str(json_dict(first).get('text'))
                            except (KeyError, IndexError, TypeError):
                                continue
                        else:
                            if 'promptFeedback' in data:
                                br = json_dict(data['promptFeedback']).get('blockReason', 'UNKNOWN')
                                logger.error(f"❌ Заблокировано: {br}")
                                return tr(lang, "ai_blocked")
                            await asyncio.sleep(backoff)
                            continue
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Сетевая ошибка: {e}")
                await asyncio.sleep(backoff)
                continue
            except Exception as e:
                logger.error(f"Непредвиденная ошибка: {e}")
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

            # ---- html version parsing ----
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
