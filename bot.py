import asyncio
import logging
import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import Message, Update

# --- Конфиг ---
# 👇 НОВЫЙ ТОКЕН ВСТАВЛЕН СЮДА 👇
BOT_TOKEN = os.getenv("BOT_TOKEN", "1780243330:SOkDRzNivZw2gpq5cTRQCqjn_zWJwr_jL-Y")
API_BASE = os.getenv("API_BASE", "https://misugram.cloud-ip.cc")

# --- Flask (веб-сервер для Render) ---
app = Flask(__name__)

# --- Подключение к шлюзу ---
session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE))
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# --- Хендлер (что бот отвечает) ---
@dp.message(F.text)
async def handle_text(message: Message):
    await message.reply(
        f"Твой ID: `{message.from_user.id}`\n"
        f"Имя: {message.from_user.full_name}"
    )

# --- Эндпоинты для Render ---
@app.route('/')
@app.route('/health')
def health():
    return "Bot is running", 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    # Telegram будет присылать сюда сообщения
    if request.headers.get('content-type') == 'application/json':
        json_data = await request.get_json()
        update = Update.model_validate(json_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return "OK", 200
    return "Bad Request", 400

# --- Запуск ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Получаем URL, который выдал Render (он автоматом прокидывает его в env)
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        # Устанавливаем вебхук
        asyncio.run(bot.set_webhook(webhook_url, drop_pending_updates=True))
        print(f"Вебхук установлен на: {webhook_url}")
    else:
        print("⚠️ RENDER_EXTERNAL_URL не найден. Если ты локально — вебхук не встанет.")

    # Запускаем Flask для Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
