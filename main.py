import asyncio
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# --- AHO USHYIRA HELPER FUNCTIONS ZAWE (fetch_xauusd_candles & detect_eqh_eql_sweeps) ---

async def automatic_smc_monitor(app):
    """Automatic background loop running every 2 minutes for EQH/EQL Sweeps & Alerts"""
    global USER_CHAT_ID, last_alert_state
    
    while True:
        try:
            await asyncio.sleep(120) # Monitor buri minota 2
            
            if USER_CHAT_ID is None:
                continue

            candles, _ = fetch_xauusd_candles(interval="1m", range_val="1d")
            if not candles:
                continue

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
                    await app.bot.send_message(chat_id=USER_CHAT_ID, text=msg, parse_mode="Markdown")

                elif sweep_data['type'] == 'BEARISH_SWEEP' and last_alert_state != 'BEAR_SWEEP':
                    last_alert_state = 'BEAR_SWEEP'
                    msg = (
                        f"🚨 *HIGH-PROBABILITY SMC SELL ALERT!*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔥 *EQH Liquidity Swept:* ${sweep_data['level']:.2f}\n"
                        f"✅ *Validation:* Retail OBs/FVGs Cleared & Swept!\n"
                        f"⚡ *Fair Value Gap (FVG):* Imbalance Confirmed\n\n"
                        f"📍 *VALID ENTRY:* ${sweep_data['entry']:.2f}\n"
                        f"🛑 *Stop Loss (SL):* ${sweep_data['sl']:.2f}\n"
                        f"🎯 *Take Profit 1 (TP1):* ${sweep_data['tp1']:.2f}\n"
                        f"🚀 *Take Profit 2 (TP2):* ${sweep_data['tp2']:.2f}"
                    )
                    await app.bot.send_message(chat_id=USER_CHAT_ID, text=msg, parse_mode="Markdown")

        except Exception as e:
            await asyncio.sleep(5)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id

    await update.message.reply_text(
        "👋 *EQH/EQL Liquidity Sweep Bot Yagutangijwe!*\n\n"
        "Bot iragenzura neza niba Order Blocks/FVGs zatsinzwe (Swept) mbere yo kuguha Signal nyayo!",
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
        f"🛡️ *Status:* Utégereje ko isoko riswipinga izi Liquidity Levels mbere yo gufata icyerekezo gipya!"
    )
    await update.message.reply_text(report, parse_mode="Markdown")

def main():
    while True:
        try:
            app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

            app.add_handler(CommandHandler("start", start_command))
            app.add_handler(CommandHandler("analysis", analysis_command))

            loop = asyncio.get_event_loop()
            loop.create_task(automatic_smc_monitor(app))

            print("🚀 EQH/EQL Sweep SMC Bot is Active!")
            app.run_polling()
        except Exception as e:
            print(f"Bot restart: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
