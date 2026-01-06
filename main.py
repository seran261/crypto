import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_TOKEN, SYMBOLS
from data_fetcher import fetch_ltf_price
from signal_generator import generate_signal
from telegram_notifier import send_mode_menu, handle_buttons, send_signal

CHAT_IDS = set()

async def start(update, context):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("🤖 OKX Smart Signal Bot Live")
    await send_mode_menu(update, context)

async def signal_loop(app):
    while True:
        for chat_id in list(CHAT_IDS):
            for symbol in SYMBOLS:
                price, vol = fetch_ltf_price(symbol)
                signal = generate_signal(symbol, price, vol, chat_id)
                if signal:
                    await send_signal(app.bot, chat_id, signal)
        await asyncio.sleep(30)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", send_mode_menu))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    async def post_init(app):
        asyncio.create_task(signal_loop(app))

    app.post_init = post_init
    app.run_polling()

if __name__ == "__main__":
    main()
