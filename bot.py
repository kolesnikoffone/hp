import os
import logging
import asyncio
from telegram import Update
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

# Хранилище спам-слов
spam_words = set()

# Обработчик команды /spam
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово или фразу для добавления в спам.")
        return
    phrase = " ".join(context.args).lower()
    spam_words.add(phrase)
    await update.message.reply_text(f"🚫 Добавлено в спам: {phrase}")

# Обработчик команды /unspam
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово или фразу для удаления из спама.")
        return
    phrase = " ".join(context.args).lower()
    if phrase in spam_words:
        spam_words.remove(phrase)
        await update.message.reply_text(f"✅ Удалено из спама: {phrase}")
    else:
        await update.message.reply_text(f"ℹ️ Фраза '{phrase}' не найдена в списке спама.")

# Обработчик команды /spamlist
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        await update.message.reply_text("📃 Спам-слова: " + ", ".join(spam_words))

# Проверка текста и капшена сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_variants = []

    if update.message.text:
        text_variants.append(update.message.text.lower())
    if update.message.caption:
        text_variants.append(update.message.caption.lower())

    if update.message.reply_to_message:
        if update.message.reply_to_message.text:
            text_variants.append(update.message.reply_to_message.text.lower())
        if update.message.reply_to_message.caption:
            text_variants.append(update.message.reply_to_message.caption.lower())

    if update.message.forward_from:
        if update.message.text:
            text_variants.append(update.message.text.lower())
        if update.message.caption:
            text_variants.append(update.message.caption.lower())

    for text in text_variants:
        for spam in spam_words:
            if spam in text:
                try:
                    await context.bot.delete_message(chat_id=update.message.chat_id,
                                                     message_id=update.message.message_id)
                    logger.info(f"💔 Удалено сообщение: {text}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении: {e}")
                return

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
