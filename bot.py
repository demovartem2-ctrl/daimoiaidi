import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.enums import ParseMode
from aiogram.filters import Command

# --- Конфиг ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "1780243330:SOkDRzNivZw2gpq5cTRQCqjn_zWJwr_jL-Y")
API_BASE = os.getenv("API_BASE", "https://misugram.cloud-ip.cc")

# --- Подключение к шлюзу ---
session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE))
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    # Тег <code> делает текст копируемым в один клик
    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Твой ID (нажми, чтобы скопировать):\n"
        f"<code>{user_id}</code>"
    )
    await message.answer(text)

# --- Ответ на любой текст (тоже с копированием) ---
@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    await message.reply(
        f"Твой ID:\n<code>{user_id}</code>"
    )

# --- Веб-сервер для Render ---
async def health(request):
    return web.Response(text="Bot is running")

async def on_startup(bot: Bot):
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logging.info(f"Вебхук установлен: {webhook_url}")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=f"/{BOT_TOKEN}")
    setup_application(app, dp, bot=bot)
    
    dp.startup.register(on_startup)
    
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logging.info(f"Сервер запущен на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
