import json
import logging
import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init FastAPI
fastapi_app = FastAPI()

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

# Startup and shutdown
@fastapi_app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.bot.delete_webhook()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info("\u2705 Webhook установлен и обработчики запущены")

@fastapi_app.on_event("shutdown")
async def on_shutdown():
    await application.bot.delete_webhook()

# Handlers

application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Бот активен...")))

application.add_handler(CommandHandler("spam", lambda update, context: (
    spam_words.extend(context.args) or save_spamlist(spam_words) or update.message.reply_text(f"\ud83d\ude97 Добавлено в спам: {context.args}")
    if context.args else update.message.reply_text("\u26a0\ufe0f Укажи слово для добавления в спам!")
)))

application.add_handler(CommandHandler("unspam", lambda update, context: (
    [spam_words.remove(word) for word in context.args if word in spam_words] or save_spamlist(spam_words) or update.message.reply_text(f"\ud83d\ude9a Удалено из спама: {context.args}")
)))

application.add_handler(CommandHandler("spamlist", lambda update, context: update.message.reply_text(
    f"Список спам-слов: {', '.join(spam_words) if spam_words else 'Пусто'}"
)))

application.add_handler(MessageHandler(filters.ALL, lambda update, context: (asyncio.create_task(handle_message(update, context)))))

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
            logger.info(f"\ud83d\udc94 Удалено сообщение: {text}")
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:fastapi_app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
