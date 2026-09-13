import os
import asyncio
import logging
import urllib.parse
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Flask Web Server setup
app = Flask(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! 👋 I am your free AI Telegram bot hosted on Render.")


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get prompt text after "/image "
    user_prompt = " ".join(context.args)

    if not user_prompt:
        await update.message.reply_text(
            "Please provide a prompt! Example:\n`/image a futuristic neon city`",
            parse_mode="Markdown"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")

    try:
        # Encode prompt into a safe URL
        encoded_prompt = urllib.parse.quote(user_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        # Send image to Telegram
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎨 **Prompt:** {user_prompt}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        await update.message.reply_text("Sorry, failed to generate the image. Please try again.")


async def handle_ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# Add Handlers to TELEGRAM_APP (Not Flask app)
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("image", generate_image))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_response))


# Health check route for Render
@app.route('/')
def home():
    return "Telegram Bot Service is active!", 200


# Webhook endpoint to receive Telegram updates
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    async def process():
        async with telegram_app:
            await telegram_app.process_update(update)

    asyncio.run(process())
    return 'OK', 200