import os
import asyncio
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google import genai
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Environment Variables (Configured on Render dashboard)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Verification check

# Initialize Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Flask Web Server setup
app = Flask(__name__)

async def start(update: Update, context):
    await update.message.reply_text("Hello! 👋 I am your free AI Telegram bot hosted on Render.")

async def handle_ai_response(update: Update, context):
    user_prompt = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_prompt
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        await update.message.reply_text("Sorry, an error occurred while generating a response.")

# Add Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_response))

# Health check route for Render
@app.route('/')
def home():
    return "Telegram Bot Service is active!", 200

# Webhook endpoint to receive Telegram updates
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    # Parse the incoming Telegram update
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    # Process async task synchronously
    async def process():
        async with telegram_app:
            await telegram_app.process_update(update)

    asyncio.run(process())
    return 'OK', 200