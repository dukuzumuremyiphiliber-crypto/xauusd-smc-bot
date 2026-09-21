import os
import threading
import time
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# --- 1. FLASK WEB SERVER (Main Process yo guhaza Render Port) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "XAUUSD SMC Bot is running!"

# --- 2. TELEGRAM & SMC TRADING BOT LOGIC ---
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
    # Aho ushyira uburyo bwawe bwo kuvumbura Liquidity Sweeps
    return None

async def automatic_smc_monitor(context: ContextTypes.DEFAULT_TYPE):
    """Automatic background loop running every 2 minutes for EQH/EQL Sweeps & Alerts"""
    global USER_CHAT_ID, last_alert_state
    
    try:
        if USER_CHAT_ID is None:
            return

        candles, _ = fetch_xauusd_candles(interval="1m", range_val="1d")
        if not candles:
            return

        sweep_data = detect_eqh_eql_sweeps(candles)

        if sweep_data:
            if sweep_data['type'] == 'BULLISH_SWEEP' and last_alert_state != 'BULL_SWEEP':
                last_alert_state = 'BULL_SWEEP'
                msg = (
                    f"🚨 *HIGH-PROBABILITY SMC BUY ALERT!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔥 *EQL Liquidity Swept:* ${sweep_data['level']:.2f}\n"
                    f"✅ *Validation:* Retail OBs/FVGs Cleared & Swept!\n"
                    f"⚡ *Fair Value Gap (FVG):* Imbalance Confirmed\n\n"
                    f"📍 *VALID ENTRY:* ${sweep_data['entry']:.2f}\n"
                    f"🛑 *Stop Loss (SL):* ${sweep_data['sl']:.2f}\n"
                    f"🎯 *Take Profit 1 (TP1):* ${sweep_data['tp1']:.2f}\n"
                    f"🚀 *Take Profit 2 (TP2):* ${sweep_data['tp2']:.2f}"
                )
                await context.bot.send_message(chat_id=USER_CHAT_ID, text=msg, parse_mode="Markdown")

    except Exception as e:
        print(f"Monitor error: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id

    await update.message.reply_text(
        "👋 *SMC Filter Bot yagutangijwe!*\n\n"
        "Irimo gukora neza mu kigo (Background Duty Active)!",
        parse_mode="Markdown"
    )

async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    candles, _ = fetch_xauusd_candles(interval="1m", range_val="1d")
    if not candles:
        await update.message.reply_text("❌ Habayeho ikosa mu kura data z'isoko.")
        return

    current_price = candles[-1]['close']

    report = (
        f"📊 *XAUUSD Real Spot Analysis*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Current Price:* ${current_price:.2f}\n"
        f"🎯 *Status:* Live & Monitoring"
    )
    await update.message.reply_text(report, parse_mode="Markdown")

def run_telegram_bot():
    """Gutangiza Telegram Bot muri Background Thread nta nzitizi"""
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("analyze", analysis_command))
        
        # Job queue yo kugenzura isoko buri minota 2
        application.job_queue.run_repeating(automatic_smc_monitor, interval=120, first=10)
        
        print("Telegram Bot is running...")
        application.run_polling()
    except Exception as e:
        print(f"Error starting Telegram Bot: {e}")

# Tangiza Telegram bot muri background thread
threading.Thread(target=run_telegram_bot, daemon=True).start()

# --- 3. RUN FLASK (Main Process) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
