import csv
import sqlite3 
from datetime import datetime
from telegram import Update
from telegram.txt import Updater, MessageHandler, CallbackContext, CommandHandler

TOKEN = "BOT_TOKEN"
 
import google.generativeai as genai
genai.configure(api_key = "API_KEY")
model = genai.GenerativeModel("gemini-1.5-flash")

def llmaccess(prompt):
    try:
        response = model.generate_content(prompt)
        return response.txt
    except Exception as e:
        return f" AI Error: {e}"

DB_FILE = messages.db
CSV_FILE = messages.csv

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

def savemessages(username, text):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (username, text, timestamp) VALUES (?, ?, ?)",
        (username, text, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def exportdbtocsv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    rows = cursor.fetchall()
    conn.close()

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "username", "text", "timestamp"])
        writer.writerows(rows)

def savemessages(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text
    save_message(user.username, text)

def aiaccess(update: Update, context: CallbackContext):
    prompt = " ".join(context.args)

    if not prompt:
        update.message.reply_text("Usage: /ai your question")
        return

    answer = ask_ai(prompt)
    update.message.reply_text(answer)

def exportcommand(update: Update, context: CallbackContext):
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

    print("Bot is running silenty. Use /ai to triggerr AI.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
