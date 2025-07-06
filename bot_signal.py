
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime, time, timedelta
import holidays
import random

# CONFIGURATION
BOT_TOKEN = "7771866391:AAFI4fcnh24DnEahRO0OlDZk9tFQLYxc47U"
CHANNEL_ID = "@kilechou_trader"

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Etats pour ConversationHandler
CHOOSING_ACTION, ASK_ENTRY, ASK_TP1, ASK_TP2, ASK_TP3, ASK_SL, ASK_IMAGE = range(7)
user_data_store = {}

# Variantes de messages
TP_MESSAGES = {
    "tp1": ["🎯 TP1 hit! Let’s keep it going!", "💥 TP1 reached! Stay focused!"],
    "tp2": ["🔥 TP2 smashed! Momentum strong!", "💪 TP2 locked in!"],
    "tp3": ["🚀 TP3 reached! Pure profit!", "🎉 TP3 done! Well played!"],
    "sl":  ["❌ SL hit. We don’t win every time – stay focused!", "😓 SL touched. That’s the game – we learn and move."]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send 'gold' to create a signal.
Send 'tp1', 'tp2', 'tp3', or 'sl' to publish updates.")

async def handle_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buy or Sell?", reply_markup=ReplyKeyboardMarkup([["Buy", "Sell"]], one_time_keyboard=True))
    return CHOOSING_ACTION

async def set_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id] = {"action": update.message.text}
    await update.message.reply_text("Entry price?")
    return ASK_ENTRY

async def set_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["entry"] = update.message.text
    await update.message.reply_text("TP1?")
    return ASK_TP1

async def set_tp1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["tp1"] = update.message.text
    await update.message.reply_text("TP2?")
    return ASK_TP2

async def set_tp2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["tp2"] = update.message.text
    await update.message.reply_text("TP3?")
    return ASK_TP3

async def set_tp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["tp3"] = update.message.text
    await update.message.reply_text("Stop Loss (SL)?")
    return ASK_SL

async def set_sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["sl"] = update.message.text
    await update.message.reply_text("Do you want to add an image? (yes/no)")
    return ASK_IMAGE

async def set_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    want_image = update.message.text.lower()
    chat_id = update.effective_chat.id
    data = user_data_store.get(chat_id)

    signal = f"""
📊 *{data['action']} XAUUSD*
💰 *Entry:* {data['entry']}
🎯 *TP1:* {data['tp1']}
🎯 *TP2:* {data['tp2']}
🎯 *TP3:* {data['tp3']}
🛑 *SL:* {data['sl']}
⚠️ Risk management is key!
    """
    if want_image == "yes":
        await update.message.reply_text("Please send the image now.")
        context.user_data["pending_signal"] = signal
        return ConversationHandler.END
    else:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=signal, parse_mode="Markdown")
        return ConversationHandler.END

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "pending_signal" in context.user_data:
        caption = context.user_data.pop("pending_signal")
        await update.message.photo[-1].get_file().download_to_drive("temp.jpg")
        with open("temp.jpg", "rb") as img:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=img, caption=caption, parse_mode="Markdown")

async def keyword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text in TP_MESSAGES:
        msg = random.choice(TP_MESSAGES[text])
        await context.bot.send_message(chat_id=CHANNEL_ID, text=msg)

async def morning_news(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().date()
    is_holiday = today in holidays.US()
    if is_holiday:
        msg = "🇺🇸 US Holiday today – XAUUSD might be slow.
Good morning team 👋"
    else:
        msg = "🌅 Good morning team 👋
No major news today for XAUUSD – trade safe!"
    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("(?i)^gold$"), handle_gold)],
        states={
            CHOOSING_ACTION: [MessageHandler(filters.TEXT, set_action)],
            ASK_ENTRY: [MessageHandler(filters.TEXT, set_entry)],
            ASK_TP1: [MessageHandler(filters.TEXT, set_tp1)],
            ASK_TP2: [MessageHandler(filters.TEXT, set_tp2)],
            ASK_TP3: [MessageHandler(filters.TEXT, set_tp3)],
            ASK_SL: [MessageHandler(filters.TEXT, set_sl)],
            ASK_IMAGE: [MessageHandler(filters.TEXT, set_image)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.PHOTO, image_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), keyword_handler))

    # Schedule morning job at 6:00 GMT+2 (4:00 UTC)
    app.job_queue.run_daily(morning_news, time=time(hour=4, minute=0))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
