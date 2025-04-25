
import os
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from fastapi import FastAPI, Request
from starlette.responses import Response
import uvicorn

print("🚀 Бот запускается...")

BANNED_FILE = "banned_words.json"

def load_banned_words():
    if not os.path.exists(BANNED_FILE):
        print("📂 Нет файла со стоп-словами. Создаём новый.")
        return []
    with open(BANNED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_banned_words(words):
    with open(BANNED_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

BANNED_WORDS = load_banned_words()

async def delete_bad_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message and update.message.text:
            text = update.message.text.lower()
            print(f"🔍 Проверяем сообщение: {text}")
            for word in BANNED_WORDS:
                if word in text:
                    await update.message.delete()
                    print(f"🗑 Удалено сообщение за слово: {word}")
                    break
    except Exception as e:
        print(f"❌ Ошибка в delete_bad_messages: {e}")

async def add_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("📥 Команда /spam:", context.args)
        if not context.args:
            await update.message.reply_text("⚠️ Используй: /spam <слово или фраза>")
            return
        phrase = " ".join(context.args).lower()
        if phrase not in BANNED_WORDS:
            BANNED_WORDS.append(phrase)
            save_banned_words(BANNED_WORDS)
            await update.message.reply_text(f"✅ Добавлено в спам: {phrase}")
        else:
            await update.message.reply_text("🔁 Уже в списке спама.")
    except Exception as e:
        print(f"❌ Ошибка в add_spam: {e}")

async def remove_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("📥 Команда /unspam:", context.args)
        if not context.args:
            await update.message.reply_text("⚠️ Используй: /unspam <слово>")
            return
        phrase = " ".join(context.args).lower()
        if phrase in BANNED_WORDS:
            BANNED_WORDS.remove(phrase)
            save_banned_words(BANNED_WORDS)
            await update.message.reply_text(f"❌ Удалено из спама: {phrase}")
        else:
            await update.message.reply_text("❗ Такого слова нет в списке.")
    except Exception as e:
        print(f"❌ Ошибка в remove_spam: {e}")

async def list_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("📥 Команда /spamlist")
        if not BANNED_WORDS:
            await update.message.reply_text("📭 Список спама пуст.")
        else:
            text = "\n".join(f"- {w}" for w in BANNED_WORDS)
            await update.message.reply_text(f"📃 Список спама:\n{text}")
    except Exception as e:
        print(f"❌ Ошибка в list_spam: {e}")

# 🔁 Периодический лог
async def health_ping():
    while True:
        print("💓 Бот активен...")
        await asyncio.sleep(30)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), delete_bad_messages))
application.add_handler(CommandHandler("spam", add_spam))
application.add_handler(CommandHandler("unspam", remove_spam))
application.add_handler(CommandHandler("spamlist", list_spam))

fastapi_app = FastAPI()

@fastapi_app.get("/")
async def root():
    return {"status": "ok", "message": "Bot is running"}

@fastapi_app.on_event("startup")
async def startup():
    print("🌐 FastAPI startup")
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL + "/webhook")
    await application.start()
    asyncio.create_task(health_ping())
    print("✅ Webhook установлен и приложение запущено")

@fastapi_app.on_event("shutdown")
async def shutdown():
    print("🛑 FastAPI shutdown triggered — Render завершает процесс")
    await application.stop()
    await application.bot.delete_webhook()
    print("🧹 Webhook удалён, завершение")

@fastapi_app.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        print("📩 Пришло новое обновление")
    except Exception as e:
        print(f"❌ Ошибка в webhook: {e}")
    return Response(status_code=200)

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
