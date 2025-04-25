import json
import logging
import os
from fastapi import FastAPI, Request
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + "/webhook"
SPAM_FILE = "spamlist.json"

# Load spam list
def load_spamlist():
    if os.path.exists(SPAM_FILE):
        with open(SPAM_FILE, "r") as f:
            return json.load(f)
    return []

# Save spam list
def save_spamlist(words):
    with open(SPAM_FILE, "w") as f:
        json.dump(words, f)

spam_words = load_spamlist()

# Telegram application
application = Application.builder().token(TOKEN).build()

# Init FastAPI
fastapi_app = FastAPI()

@fastapi_app.on_event("startup")
async def on_startup():
    try:
        await application.initialize()
        await application.bot.delete_webhook()
        await application.bot.set_webhook(WEBHOOK_URL)
        logger.info("✅ Webhook установлен и обработчики запущены")
    except Exception as e:
        logger.error(f"❌ Ошибка при старте: {e}")

@fastapi_app.on_event("shutdown")
async def on_shutdown():
    try:
        await application.bot.delete_webhook()
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении: {e}")

# Healthcheck
@fastapi_app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Root ping for Render
@fastapi_app.get("/")
async def root():
    return {"status": "alive"}

# Webhook endpoint
@fastapi_app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}\nUpdate: {data if 'data' in locals() else 'нет данных'}")
    return "OK"

# Spam command handler
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args:
            spam_words.extend(context.args)
            save_spamlist(spam_words)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🚫 Добавлено в спам: {context.args}")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Укажи слово для добавления в спам!")
    except TelegramError as e:
        logger.error(f"Ошибка в /spam: {e}")

# Unspam command handler
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args:
            removed = [word for word in context.args if word in spam_words]
            for word in removed:
                spam_words.remove(word)
            save_spamlist(spam_words)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Удалено из спама: {removed}")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Укажи слово для удаления из спама!")
    except TelegramError as e:
        logger.error(f"Ошибка в /unspam: {e}")

# Spamlist command handler
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = f"📋 Список спам-слов: {', '.join(spam_words) if spam_words else 'Пусто'}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    except TelegramError as e:
        logger.error(f"Ошибка в /spamlist: {e}")

# Message processing logic
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.message or update.edited_message
    if not message:
        logger.warning(f"❗️ Пропущен update без message: {update}")
        return

    try:
        text = message.text or message.caption or ""
        logger.info(f"📩 Пришло сообщение: {text}")

        if message.forward_date or message.forward_from:
            logger.info("📨 Обнаружено пересланное сообщение")

        if any(word.lower() in text.lower() for word in spam_words):
            await message.delete()
            logger.info(f"💔 Удалено сообщение: {text}")
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения: {e}")

# Register command handlers
application.add_handler(CommandHandler("spam", handle_spam))
application.add_handler(CommandHandler("unspam", handle_unspam))
application.add_handler(CommandHandler("spamlist", handle_spamlist))

# Message handler
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# Global error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"🚨 Unhandled exception: {context.error}\nUpdate: {update}")

application.add_error_handler(error_handler)
