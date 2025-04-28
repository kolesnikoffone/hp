import logging
import os
import asyncio
from typing import List
from fastapi import FastAPI
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# Логи
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bot")

# Инициализация бота
application = Application.builder().token(TOKEN).build()

# FastAPI для healthcheck
fastapi_app = FastAPI()

# Файл для спам-слов
SPAM_FILE = "spam_words.txt"

def load_spam_words() -> List[str]:
    if not os.path.exists(SPAM_FILE):
        return []
    with open(SPAM_FILE, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

def save_spam_words(words: List[str]):
    with open(SPAM_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(words))

# Команда /spam
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите слово или фразу для добавления в спам.")
        return
    spam_word = " ".join(context.args).lower()
    words = load_spam_words()
    if spam_word not in words:
        words.append(spam_word)
        save_spam_words(words)
        await update.message.reply_text(f"✅ Добавлено в спам: {spam_word}")
    else:
        await update.message.reply_text(f"⚠️ Уже в списке спама: {spam_word}")

# Команда /unspam
async def unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите слово или фразу для удаления из спама.")
        return
    spam_word = " ".join(context.args).lower()
    words = load_spam_words()
    if spam_word in words:
        words.remove(spam_word)
        save_spam_words(words)
        await update.message.reply_text(f"✅ Удалено из спама: {spam_word}")
    else:
        await update.message.reply_text(f"⚠️ Этого нет в списке спама: {spam_word}")

# Команда /spamlist
async def spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = load_spam_words()
    if not words:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        text = "\n".join(f"• {word}" for word in words)
        await update.message.reply_text(f"📋 Список спам-слов:\n{text}")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.message
    if not message:
        return

    text = ""
    if message.text:
        text = message.text.lower()
    elif message.caption:
        text = message.caption.lower()

    if not text:
        return

    spam_words = load_spam_words()

    for phrase in spam_words:
        if phrase in text:
            try:
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                logger.info(f"💔 Удалено сообщение: {text}")
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")
            return

    logger.info(f"📩 Пришло сообщение: {text}")

# Хендлеры
application.add_handler(CommandHandler("spam", spam))
application.add_handler(CommandHandler("unspam", unspam))
application.add_handler(CommandHandler("spamlist", spamlist))
application.add_handler(MessageHandler(filters.TEXT | filters.CaptionedMediaGroup, handle_message))

# FastAPI события старта и остановки
@fastapi_app.on_event("startup")
async def startup():
    asyncio.create_task(application.initialize())
    await application.start_polling()
    logger.info("✅ Polling запущен и бот слушает обновления")

@fastapi_app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()

# healthcheck
@fastapi_app.get("/healthz")
async def health_check():
    return {"status": "ok"}
