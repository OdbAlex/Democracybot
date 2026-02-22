# =============================================================================
# bot.py  (~35 Zeilen)
# Starten mit: python bot.py  (aus dem src/ Ordner)
# =============================================================================

import os
from dotenv import load_dotenv
from telegram.ext import (ApplicationBuilder, CommandHandler,
                           MessageHandler, filters)
from handlers import (cmd_start, cmd_ja, cmd_nein, cmd_session,
                      cmd_beenden, cmd_status, handle_message)

load_dotenv(dotenv_path="../config/.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN fehlt in config/.env!")

def main():
    print("🤖 DemocracyBot wird gestartet…")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("ja",      cmd_ja))
    app.add_handler(CommandHandler("nein",    cmd_nein))
    app.add_handler(CommandHandler("session", cmd_session))
    app.add_handler(CommandHandler("beenden", cmd_beenden))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Läuft. Abbrechen mit Ctrl+C.")
    app.run_polling()

if __name__ == "__main__":
    main()
