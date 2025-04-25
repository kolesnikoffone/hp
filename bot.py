import json
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

# Lifespan event for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    await application.initialize()
    await application.bot.delete_webhook()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook установлен и обработчики запущены")
    yield
    await application.bot.delete_webhook()

# Init FastAPI with lifespan
fastapi_app = FastAPI(lifespan=lifespan)

# Healthcheck
@fastapi_app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Webhook endpoint
@fastapi_app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
    return "OK"

# Handlers
application.add_handler(CommandHandler("spam", lambda update, context: (
    spam_words.extend(context.args) or save_spamlist(spam_words) or update.message.reply_text(f"Добавлено в спам: {context.args}")
    if context.args else update.message.reply_text("⚠️ Укажи слово для добавления в спам!")
)))

application.add_handler(CommandHandler("unspam", lambda update, context: (
    [spam_words.remove(word) for word in context.args if word in spam_words],
    save_spamlist(spam_words),
    update.message.reply_text(f"Удалено из спама: {context.args}")
)[-1] if context.args else update.message.reply_text("⚠️ Укажи слово для удаления из спама!")
))

application.add_handler(CommandHandler("spamlist", lambda update, context: update.message.reply_text(f"Список спам-слов: {', '.join(spam_words) if spam_words else 'Пусто'}")))

application.add_handler(MessageHandler(filters.ALL, lambda update, context: asyncio.create_task(handle_message(update, context))))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.message or update.edited_message
    if not message:
        return

    text = message.text or message.caption or ""

    # Check forwarded messages
    if message.forward_date or message.forward_from:
        text = (message.text or message.caption) or ""

    if any(word.lower() in text.lower() for word in spam_words):
        try:
            await message.delete()
            logger.info(f"💔 Удалено сообщение: {text}")
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение: {e}")
