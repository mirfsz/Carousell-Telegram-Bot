from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# States for the ConversationHandler
MAIN_MENU, SEARCH, VIEWING_RESULTS, FILTERING, SET_PRICE_ALERT, SET_FREQUENCY, VIEW_TRACKED_ITEMS, EDIT_TRACKED_ITEM = range(8)

async def send_typing_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

async def update_message(update: Update, text: str, reply_markup: InlineKeyboardMarkup = None):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def format_price(price: str) -> float:
    try:
        return float(price.replace('S$', '').replace(',', ''))
    except ValueError:
        return 0.0