import os
import logging
import asyncio
from telegram import Update, Message
from telegram.ext import (ApplicationBuilder, ContextTypes, MessageHandler,
                          CommandHandler, filters)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

# Получение токена
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

# Хранилище спам-слов и фраз
spam_words = set()

# --- Команды --- #

async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = await update.message.reply_text("❗ Укажи слово или фразу для добавления в спам.")
        await asyncio.sleep(5)
        await msg.delete()
        await update.message.delete()
        return
    phrase = " ".join(context.args).lower()
    spam_words.add(phrase)
    msg = await update.message.reply_text(f"🚫 Добавлено в спам: {phrase}")
    await asyncio.sleep(5)
    await msg.delete()
    await update.message.delete()

async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = await update.message.reply_text("❗ Укажи слово или фразу для удаления из спама.")
        await asyncio.sleep(5)
        await msg.delete()
        await update.message.delete()
        return
    phrase = " ".join(context.args).lower()
    spam_words.discard(phrase)
    msg = await update.message.reply_text(f"✅ Удалено из спама: {phrase}")
    await asyncio.sleep(5)
    await msg.delete()
    await update.message.delete()

async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        msg = await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        msg = await update.message.reply_text("📃 Спам-слова:\n" + "\n".join(spam_words))
    await asyncio.sleep(5)
    await msg.delete()
    await update.message.delete()

# --- Основная обработка сообщений --- #

def extract_text(message: Message) -> str:
    """Извлекает текст для анализа из разных типов сообщений."""
    if message.text:
        return message.text
    if message.caption:
        return message.caption
    return ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = extract_text(update.message).lower()

    # Если пересланное сообщение с подписью
    if update.message.forward_from_chat and update.message.caption:
        msg_text = update.message.caption.lower()

    logger.info(f"📩 Пришло сообщение: {msg_text}")

    if any(spam_word in msg_text for spam_word in spam_words):
        try:
            await context.bot.delete_message(chat_id=update.message.chat_id,
                                             message_id=update.message.message_id)
            logger.info(f"💔 Удалено сообщение: {msg_text}")
        except Exception as e:
            logger.error(f"Ошибка при удалении: {e}")

# --- Запуск --- #

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
