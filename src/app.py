# Kulsh GPT | v2.40.0
# by (main author): starfall-apk
# coauthor & bot hosting: pomidorka1515

"""Process entry: build the bots, register handlers, run both platforms."""

import asyncio

import discord
from discord import app_commands
from telebot.async_telebot import AsyncTeleBot

from src import discord_cmds, discord_msg, loops, media, rich, telegram
from src.util import (
    AI_KEYS,
    DISCORD_TOKEN,
    DONATIONALERTS_TOKEN,
    DS_ALLOWED_GUILD_ID,
    TG_TOKEN,
    voice_recognition_enabled,
    typed_decorator,
    logger,
    msk_datetime_str,
)

if not AI_KEYS:
    logger.critical("❌ Не найден ни один API ключ Gemini!")
    raise SystemExit(1)

tg_bot = AsyncTeleBot(TG_TOKEN)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
ds_bot = discord.Client(intents=intents)
ds_tree = app_commands.CommandTree(ds_bot)

telegram.bind(tg_bot)
rich.bind(tg_bot)
discord_cmds.bind(ds_bot)
loops.bind(ds_bot, tg_bot)


def register_telegram() -> None:
    deco = typed_decorator
    deco(tg_bot.callback_query_handler)(func=lambda call: bool(call.data and call.data.startswith("cfg:")))(telegram.handle_cfg_callback)
    deco(tg_bot.callback_query_handler)(func=lambda call: bool(call.data and call.data.startswith("menu:")))(telegram.handle_menu_callback)
    deco(tg_bot.message_handler)(commands=["start"])(telegram.handle_start)
    deco(tg_bot.message_handler)(commands=["menu"])(telegram.handle_menu)
    deco(tg_bot.message_handler)(commands=["help"])(telegram.handle_help)
    deco(tg_bot.message_handler)(commands=["status"])(telegram.handle_status)
    deco(tg_bot.message_handler)(commands=["donate"])(telegram.handle_donate)
    deco(tg_bot.message_handler)(commands=["donate_stars"])(telegram.handle_donate_stars)
    deco(tg_bot.message_handler)(commands=["credits"])(telegram.handle_credits)
    deco(tg_bot.message_handler)(commands=["togglepremiumfunctionsadmin"])(telegram.handle_toggle_premium)
    deco(tg_bot.pre_checkout_query_handler)(func=lambda query: True)(telegram.handle_pre_checkout)
    deco(tg_bot.message_handler)(content_types=["successful_payment"])(telegram.handle_successful_payment)
    deco(tg_bot.message_handler)(content_types=["photo", "video", "animation", "document", "sticker"])(media.handle_tg_media)
    deco(tg_bot.message_handler)(func=lambda m: m.text is not None, content_types=["text"])(media.handle_tg_text)


def register_discord() -> None:
    tree = ds_tree
    tree.command(name="start", description="Greeting / Приветствие")(discord_cmds.ds_slash_start)
    tree.command(name="menu", description="Menu / Меню")(discord_cmds.ds_slash_menu)
    tree.command(name="help", description="Command list / Список команд")(discord_cmds.ds_slash_help)
    tree.command(name="status", description="Bot status / Состояние бота")(discord_cmds.ds_slash_status)
    tree.command(name="donate", description="Support the project / Поддержать проект")(discord_cmds.ds_slash_donate)
    tree.command(name="credits", description="Credits balance / Баланс кредитов")(discord_cmds.ds_slash_credits)
    tree.command(name="config", description="Channel settings / Настройки канала")(discord_cmds.ds_slash_config)
    tree.command(name="logs", description="Server logs (admins) / Логи сервера (админам)")(discord_cmds.ds_slash_logs)

    @tree.command(name="avatar", description="Describe avatar / Описать аватарку")
    @app_commands.describe(user="Whose avatar to describe / Чью аватарку описать")
    async def avatar(interaction: discord.Interaction, user: discord.Member | None = None) -> None:
        await discord_cmds.ds_slash_avatar(interaction, user)

    @tree.command(name="recall", description="Recall recent media / Вспомнить недавние медиа")
    @app_commands.describe(count="How many last items / Сколько последних элементов")
    async def recall(interaction: discord.Interaction, count: int = 3) -> None:
        await discord_cmds.ds_slash_recall(interaction, count)

    @tree.command(name="search", description="Web search / Поиск в интернете")
    @app_commands.describe(query="What to search / Что искать")
    async def search(interaction: discord.Interaction, query: str) -> None:
        await discord_cmds.ds_slash_search(interaction, query)

    @tree.command(name="chart", description="Generate infographic / Сгенерировать инфографику")
    @app_commands.describe(description="Describe the chart / Опиши график")
    async def chart(interaction: discord.Interaction, description: str) -> None:
        await discord_cmds.ds_slash_chart(interaction, description)

    @tree.command(name="psl", description="Looksmaxxing analysis / Оценка внешности")
    @app_commands.describe(image="Photo / Фото", advice="Include advice / Показать рекомендации")
    async def psl(interaction: discord.Interaction, image: discord.Attachment, advice: bool = False) -> None:
        await discord_cmds.ds_slash_psl(interaction, image, advice)

    @tree.command(name="battle", description="Two-photo battle / Баттл двух фото")
    @app_commands.describe(image1="First photo / Первое фото", image2="Second photo / Второе фото")
    async def battle(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment) -> None:
        await discord_cmds.ds_slash_battle(interaction, image1, image2)

    @tree.command(name="femboy", description="Femboy Rate / Оценка фембойности")
    @app_commands.describe(image="Photo / Фото", advice="Include advice / Показать рекомендации")
    async def femboy(interaction: discord.Interaction, image: discord.Attachment, advice: bool = False) -> None:
        await discord_cmds.ds_slash_femboy(interaction, image, advice)

    @tree.command(name="femboy-battle", description="Femboy battle / Фембой-баттл")
    @app_commands.describe(image1="First photo / Первое фото", image2="Second photo / Второе фото")
    async def femboy_battle(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment) -> None:
        await discord_cmds.ds_slash_femboy_battle(interaction, image1, image2)

    ds_bot.event(discord_msg.on_message)


def register() -> None:
    register_telegram()
    register_discord()


async def main() -> None:
    register()
    asyncio.create_task(loops.random_post_loop())

    @ds_bot.event
    async def on_ready() -> None:
        logger.info(f"Discord {ds_bot.user} запущен, discord.py {discord.__version__}")
        if not voice_recognition_enabled:
            logger.info("ℹ️ Распознавание голоса отключено")
        try:
            guild = discord.Object(id=DS_ALLOWED_GUILD_ID)
            ds_tree.copy_global_to(guild=guild)
            synced = await ds_tree.sync(guild=guild)
            logger.info(f"Синхронизировано slash-команд: {len(synced)}")
        except Exception as e:
            logger.error(f"Не удалось синхронизировать slash-команды: {e}")
        asyncio.create_task(loops.series_reminder_loop())
        if DONATIONALERTS_TOKEN:
            asyncio.create_task(loops.donation_alerts_listener())

    async def start_discord() -> None:
        await ds_bot.start(DISCORD_TOKEN)

    async def start_telegram() -> None:
        await tg_bot.polling(non_stop=True)

    await asyncio.gather(start_discord(), start_telegram())


def run() -> None:
    logger.info(f">>> 🍷🗿 Кульш в эфире. МСК: {msk_datetime_str()}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()