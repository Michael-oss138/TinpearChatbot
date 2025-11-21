import os
import csv
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")

if not TOKEN:
    raise ValueError("ERROR: BOT_TOKEN is missing in your .env file")

if not API_KEY or not API_KEY.startswith("gsk_"):
    raise ValueError("ERROR: API_KEY is missing in your .env file")

client = Groq(api_key=API_KEY)

DB_FILE = "messages.db"
CSV_FILE = "messages.csv"



def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            text TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_message(username, text):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (username, text, timestamp) VALUES (?, ?, ?)",
        (username, text, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def export_to_csv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    rows = cursor.fetchall()
    conn.close()

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "username", "text", "timestamp"])
        writer.writerows(rows)



def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful Telegram bot assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {e}"



def save_only(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text
    save_message(user.username, text)


def ai_command(update: Update, context: CallbackContext):
    prompt = " ".join(context.args)

    if not prompt:
        update.message.reply_text("Usage: /ai your question")
        return

    answer = ask_ai(prompt)
    update.message.reply_text(answer)


def export_command(update: Update, context: CallbackContext):
    export_to_csv()
    with open(CSV_FILE, "rb") as f:
        update.message.reply_document(f, filename=CSV_FILE)



def main():
    init_db()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, save_only))

    dp.add_handler(CommandHandler("ai", ai_command))
    dp.add_handler(CommandHandler("export", export_command))

    print("Bot is running with GROQ... Use /ai to ask the bot.")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()