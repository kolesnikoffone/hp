import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)

# Логирование
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

# Вспомогательная функция для удаления сообщений через 5 секунд
async def delete_after_delay(bot, chat_id, message_id, delay=5):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message_id}: {e}")

# Обработчик команды /spam
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        reply = await update.message.reply_text("❗ Укажи слово для добавления в спам.")
    else:
        for word in context.args:
            spam_words.add(word.lower())
        reply = await update.message.reply_text(f"🚫 Добавлено в спам: {context.args}")
    
    asyncio.create_task(delete_after_delay(context.bot, update.message.chat_id, update.message.message_id))
    asyncio.create_task(delete_after_delay(context.bot, reply.chat_id, reply.message_id))

# Обработчик команды /unspam
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        reply = await update.message.reply_text("❗ Укажи слово для удаления из спама.")
    else:
        for word in context.args:
            spam_words.discard(word.lower())
        reply = await update.message.reply_text(f"✅ Удалено из спама: {context.args}")

    asyncio.create_task(delete_after_delay(context.bot, update.message.chat_id, update.message.message_id))
    asyncio.create_task(delete_after_delay(context.bot, reply.chat_id, reply.message_id))

# Обработчик команды /spamlist
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        reply = await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        reply = await update.message.reply_text("📃 Спам-слова: " + ", ".join(spam_words))
    
    asyncio.create_task(delete_after_delay(context.bot, update.message.chat_id, update.message.message_id))
    asyncio.create_task(delete_after_delay(context.bot, reply.chat_id, reply.message_id))

# Основной фильтр сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_variants = []
    if update.message.text:
        text_variants.append(update.message.text.lower())
    if update.message.reply_to_message and update.message.reply_to_message.text:
        text_variants.append(update.message.reply_to_message.text.lower())
    if update.message.forward_from and update.message.text:
        text_variants.append(update.message.text.lower())

    for text in text_variants:
        if any(word == text for word in spam_words) or any(f" {word} " in f" {text} " for word in spam_words):
            try:
                await context.bot.delete_message(chat_id=update.message.chat_id,
                                                 message_id=update.message.message_id)
                logger.info(f"💔 Удалено сообщение: {text}")
            except Exception as e:
                logger.error(f"Ошибка при удалении: {e}")
            break  # Если нашли хоть одно, дальше не проверяем

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
