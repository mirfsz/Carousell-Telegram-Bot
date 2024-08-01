import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from bot_handlers import (
    start, help_command, handle_main_menu, handle_search, handle_results_navigation,
    handle_filter_item, handle_set_price_alert, handle_set_frequency, stop_scheduled_search,
    view_tracked_items, handle_edit_tracked_item, handle_edit_tracked_item_input
)
from utils import MAIN_MENU, SEARCH, VIEWING_RESULTS, FILTERING, SET_PRICE_ALERT, SET_FREQUENCY, VIEW_TRACKED_ITEMS, EDIT_TRACKED_ITEM

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

def main() -> None:
    try:
        # Replace 'YOUR_BOT_TOKEN' with your actual bot token
        application = Application.builder().token('').build()
        logger.info("Bot application created successfully.")

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                MAIN_MENU: [CallbackQueryHandler(handle_main_menu)],
                SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)],
                VIEWING_RESULTS: [CallbackQueryHandler(handle_results_navigation)],
                FILTERING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filter_item)],
                SET_PRICE_ALERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_price_alert)],
                SET_FREQUENCY: [CallbackQueryHandler(handle_set_frequency)],
                VIEW_TRACKED_ITEMS: [
                    CallbackQueryHandler(handle_edit_tracked_item, pattern=r'^edit_\d+$'),
                    CallbackQueryHandler(handle_main_menu, pattern='^back_to_main$')
                ],
                EDIT_TRACKED_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_tracked_item_input)],
            },
            fallbacks=[
                CommandHandler('help', help_command),
                CommandHandler('stop', stop_scheduled_search),
                CommandHandler('start', start),
            ],
        )
        logger.info("ConversationHandler created successfully.")

        application.add_handler(conv_handler)
        logger.info("ConversationHandler added to application.")

        logger.info("Bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"An error occurred while starting the bot: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()