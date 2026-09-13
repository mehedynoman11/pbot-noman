import os
import asyncio
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google import genai

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
flask_app = Flask(__name__)

async def start(update: Update, context):
    await update.message.reply_text("Hello! Bot running on local Flask app.")

async def handle_ai(update: Update, context):
    user_prompt = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_prompt
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Error processing AI request.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai))

@flask_app.route('/')
def home():
    return "Flask local server is running!", 200

@flask_app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    # Process updates inside an async loop
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    
    async def process():
        async with telegram_app:
            await telegram_app.process_update(update)

    asyncio.run(process())
    return 'OK', 200

if __name__ == '__main__':
    flask_app.run(port=5000, debug=True)