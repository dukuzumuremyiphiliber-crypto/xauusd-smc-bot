import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# --- 1. FLASK SETUP (Guhaza Port ya Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "XAUUSD SMC Bot is running!"

# --- 2. TELEGRAM BOT SETUP ---
TELEGRAM_BOT_TOKEN = "7572240957:AAHLwJxKJR1qJo21F8NzATAlJQb21dHW8"
USER_CHAT_ID = None

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

last_alert_state = None

def fetch_xauusd_candles(interval="1m", range_val="1d"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={range_val}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()['chart']['result'][0]
            timestamps = data['timestamp']
            quotes = data['indicators']['quote'][0]
            
            candles = []
            for i in range(len(timestamps)):
                if quotes['close'][i] is not None and quotes['high'][i] is not None and quotes['low'][i] is not None:
                    candles.append({
                        'open': quotes['open'][i],
                        'high': quotes['high'][i],
                        'low': quotes['low'][i],
                        'close': quotes['close'][i]
                    })
            return candles, None
    except Exception as e:
        print(e)
    return None, None

def detect_eqh_eql_sweeps(candles):
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        "👋 *EQH/EQL Liquidity Sweep Bot Yagutangijwe neza!*",
        parse_mode="Markdown"
    )

async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    candles, _ = fetch_xauusd_candles(interval="1m", range_val="1d")
    if not candles:
        await update.message.reply_text("❌ Habayeho ikosa mu kura data z'isoko.")
        return

    current_price = candles[-1]['close']
    highs = [c['high'] for c in candles[-30:]]
    lows = [c['low'] for c in candles[-30:]]

    m15_high = max(highs)
    m15_low = min(lows)

    report = (
        f"📊 *XAUUSD SMC LIQUIDITY & STRUCTURE REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Current Spot Price:* ${current_price:.2f}\n\n"
        f"🎯 *KEY LIQUIDITY POOLS (EQH/EQL):*\n"
        f"• *Buy-Side Liquidity (BSL / EQH Target):* ${m15_high:.2f}\n"
        f"• *Sell-Side Liquidity (SSL / EQL Target):* ${m15_low:.2f}\n\n"
        f"🛡️ *Status:* Live & Monitoring"
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# Tegura Telegram Application na Handlers
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("analysis", analysis_command))

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Uburyo bwa Webhook bwakira ubutumwa bwa Telegram kuri Flask"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "ok", 200

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    """Guhuza Render na Telegram Webhook burundu"""
    render_url = request.host_url.rstrip('/')
    webhook_url = f"{render_url}/{TELEGRAM_BOT_TOKEN}"
    s = application.bot.set_webhook(url=webhook_url)
    if s:
        return f"Webhook set successfully to {webhook_url}"
    return "Webhook setup failed"

# --- 3. RUN FLASK (Main Process) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
