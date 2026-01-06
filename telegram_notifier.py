from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from user_state import set_mode
from trade_stats import win_rate

async def send_mode_menu(update, context):
    keyboard = [[
        InlineKeyboardButton("⚡ SCALP", callback_data="SCALP"),
        InlineKeyboardButton("🚀 HFT", callback_data="HFT"),
    ]]
    await update.message.reply_text(
        "Select Trading Mode:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_buttons(update, context):
    q = update.callback_query
    await q.answer()
    set_mode(q.message.chat_id, q.data)
    await q.edit_message_text(f"✅ {q.data} mode activated")

async def send_signal(bot, chat_id, s):
    wr = win_rate(s["symbol"])

    msg = (
        f"📊 {s['symbol']}\n"
        f"📈 {s['side']} | {s['mode']}\n"
        f"🎯 Entry: {s['entry']:.2f}\n"
        f"✅ TP: {s['tp']:.2f}\n"
        f"🛑 SL: {s['sl']:.2f}\n"
        f"🧠 Confidence: {s['confidence']}%\n"
        f"📊 Win Rate: {wr}%"
    )
    await bot.send_message(chat_id=chat_id, text=msg)
