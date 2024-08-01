from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from utils import send_typing_action, update_message, MAIN_MENU, SEARCH, VIEWING_RESULTS, FILTERING, SET_PRICE_ALERT, SET_FREQUENCY, VIEW_TRACKED_ITEMS, EDIT_TRACKED_ITEM
from scraper import scrape_carousell_async
import logging
import os

logger = logging.getLogger(__name__)

RESULTS_PER_PAGE = 5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} started the bot or returned to main menu")

        instructions = (
            "👋 Welcome to the Carousell Search Bot! 🛍️\n\n"
            "Here's what I can do for you:\n"
            "1. 🔍 Search Carousell for items\n"
            "2. 💰 Set price alerts for great deals\n"
            "3. 🕒 Schedule regular searches\n"
            "4. 📋 Manage your tracked items\n\n"
            "Let's get started! What would you like to do?"
        )
        message = await context.bot.send_message(chat_id=user_id, text=instructions, parse_mode=ParseMode.HTML)
        await context.bot.pin_chat_message(chat_id=user_id, message_id=message.message_id)

        return await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in start function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred. Please try again later.")
        return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        keyboard = [
            [InlineKeyboardButton("🔍 Search Carousell", callback_data='search')],
            [InlineKeyboardButton("💰 Set Price Alert", callback_data='set_alert')],
            [InlineKeyboardButton("🕒 Schedule Searches", callback_data='set_frequency')],
            [InlineKeyboardButton("📋 View Tracked Items", callback_data='view_tracked')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update_message(update, "What would you like to do? Choose an option below:", reply_markup=reply_markup)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in show_main_menu function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        logger.info(f"User {update.effective_user.id} selected option: {query.data}")
        if query.data == 'search':
            await update_message(update, "What are you looking for on Carousell? Type your search term below.")
            return SEARCH
        elif query.data == 'set_alert':
            await update_message(update, "Let's set up a price alert! What item are you interested in?")
            context.user_data['setting_alert'] = True
            return SET_PRICE_ALERT
        elif query.data == 'set_frequency':
            keyboard = [
                [InlineKeyboardButton("Every 30 minutes", callback_data='frequency_30')],
                [InlineKeyboardButton("Hourly", callback_data='frequency_60')],
                [InlineKeyboardButton("Daily", callback_data='frequency_1440')],
                [InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update_message(update, "How often should I search for you? Pick an option:", reply_markup=reply_markup)
            return SET_FREQUENCY
        elif query.data == 'view_tracked':
            return await view_tracked_items(update, context)
        elif query.data == 'help':
            return await help_command(update, context)
        elif query.data == 'back_to_main':
            return await show_main_menu(update, context)
        else:
            logger.warning(f"Unexpected callback data: {query.data}")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in handle_main_menu function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred. Please try again later.")
        return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        logger.info(f"User {update.effective_user.id} requested help")
        help_text = (
            "Here's a quick guide to using the Carousell Search Bot:\n\n"
            "🔍 <b>Search Carousell</b>: Find items you're interested in\n"
            "💰 <b>Set Price Alert</b>: Get notified about great deals\n"
            "🕒 <b>Schedule Searches</b>: Set up automatic searches (30 mins, hourly, or daily)\n"
            "📋 <b>View Tracked Items</b>: Manage your saved searches and alerts\n\n"
            "Ready to get started? Just tap a button below!"
        )
        keyboard = [
            [InlineKeyboardButton("🔍 Start Searching", callback_data='search')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update_message(update, help_text, reply_markup=reply_markup)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in help_command function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        search_term = update.message.text
        logger.info(f"User {update.effective_user.id} searching for: {search_term}")
        await update_message(update, f"🔍 Searching for '{search_term}' on Carousell... This might take a moment.")
        await send_typing_action(context, update.effective_chat.id)

        results, filepath = await scrape_carousell_async(search_term)

        if results:
            context.user_data['search_results'] = results
            context.user_data['current_page'] = 0
            context.user_data['filtered_out'] = set()  # Store filtered out item IDs
            await show_results_page(update, context)

            # Send CSV file if available
            if filepath:
                await context.bot.send_document(update.effective_chat.id, document=open(filepath, 'rb'),
                                                filename=os.path.basename(filepath))

            return VIEWING_RESULTS
        else:
            await update_message(update, "😔 I couldn't find any results for that search. Want to try something else?")
            return await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in handle_search function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while searching. Please try again later.")
        return await show_main_menu(update, context)

async def show_results_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        results = context.user_data['search_results']
        page = context.user_data['current_page']
        filtered_out = context.user_data['filtered_out']

        start_idx = page * RESULTS_PER_PAGE
        end_idx = start_idx + RESULTS_PER_PAGE
        page_results = results[start_idx:end_idx]

        message = "Search Results:\n\n"
        for i, item in enumerate(page_results, start=start_idx + 1):
            if i - 1 in filtered_out:
                message += "🚫 "  # Mark filtered items
            message += f"{i}. {item['name']} - {item['price']}\n"
            message += f"   Seller: {item['username']}\n\n"

        keyboard = []
        if page > 0:
            keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data="prev_page"))
        if end_idx < len(results):
            keyboard.append(InlineKeyboardButton("Next ➡️", callback_data="next_page"))

        keyboard = [keyboard]  # Wrap in another list for row layout
        keyboard.append([InlineKeyboardButton("🔍 New Search", callback_data="new_search")])
        keyboard.append([InlineKeyboardButton("🚫 Filter/Unfilter Item", callback_data="filter_item")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update_message(update, message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in show_results_page function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while displaying results. Please try again later.")

async def handle_results_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        if query.data == "prev_page":
            context.user_data['current_page'] -= 1
        elif query.data == "next_page":
            context.user_data['current_page'] += 1
        elif query.data == "new_search":
            await update_message(update, "What would you like to search for?")
            return SEARCH
        elif query.data == "filter_item":
            await update_message(update, "Enter the number of the item you want to filter out or unfilter:")
            return FILTERING
        elif query.data == "back_to_main":
            return await show_main_menu(update, context)

        await show_results_page(update, context)
        return VIEWING_RESULTS
    except Exception as e:
        logger.error(f"Error in handle_results_navigation function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred. Please try again later.")
        return await show_main_menu(update, context)

async def handle_filter_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        item_number = int(update.message.text) - 1
        filtered_out = context.user_data['filtered_out']

        if item_number in filtered_out:
            filtered_out.remove(item_number)
            await update_message(update, f"Item {item_number + 1} has been unfiltered.")
        else:
            filtered_out.add(item_number)
            await update_message(update, f"Item {item_number + 1} has been filtered out.")

        await show_results_page(update, context)
        return VIEWING_RESULTS
    except ValueError:
        await update_message(update, "Please enter a valid item number.")
        return FILTERING
    except Exception as e:
        logger.error(f"Error in handle_filter_item function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred. Please try again later.")
        return await show_main_menu(update, context)

async def handle_set_price_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        logger.info(f"User {update.effective_user.id} setting price alert")
        if context.user_data.get('setting_alert'):
            context.user_data['alert_item'] = update.message.text
            await update_message(update,
                                 f"Got it! You're looking for '{update.message.text}'. Now, what's the maximum price you're willing to pay? (e.g., 50 for S$50)")
            context.user_data['setting_alert'] = False
            return SET_PRICE_ALERT
        else:
            try:
                max_price = float(update.message.text)
                search_term = context.user_data['alert_item']

                if 'tracked_items' not in context.user_data:
                    context.user_data['tracked_items'] = []

                context.user_data['tracked_items'].append({'name': search_term, 'price': max_price})

                keyboard = [
                    [InlineKeyboardButton("Set up scheduled search", callback_data='set_frequency')],
                    [InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update_message(update,
                                     f"✅ Price alert set for '{search_term}' at S${max_price:.2f}. Would you like to set up a scheduled search for this item?",
                                     reply_markup=reply_markup)
                return MAIN_MENU
            except ValueError:
                await update_message(update,
                                     "Oops! That doesn't look like a valid price. Please enter a number (e.g., 50 for S$50).")
                return SET_PRICE_ALERT
    except Exception as e:
        logger.error(f"Error in handle_set_price_alert function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while setting the price alert. Please try again later.")
        return await show_main_menu(update, context)

# ... (previous code remains the same)

async def handle_set_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        logger.info(f"User {update.effective_user.id} setting search frequency: {query.data}")
        if query.data.startswith('frequency_'):
            minutes = int(query.data.split('_')[1])
            context.user_data['search_frequency'] = minutes
            search_term = context.user_data.get('alert_item', 'your item')
            max_price = context.user_data.get('max_price', None)

            job_queue = context.job_queue
            chat_id = update.effective_chat.id

            # Remove existing job if any
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            # Schedule new job
            new_job = job_queue.run_repeating(scheduled_search, interval=minutes * 60, first=10, chat_id=chat_id,
                                              name=str(chat_id),
                                              data={'search_term': search_term, 'max_price': max_price})
            context.chat_data['job'] = new_job

            frequency_text = "every 30 minutes" if minutes == 30 else "hourly" if minutes == 60 else "daily"
            message = (f"✅ Great! I've set up a scheduled search for '{search_term}' {frequency_text}. "
                       f"I'll check Carousell {frequency_text} and let you know if I find any matching items.")
            if max_price:
                message += f" I'll only notify you about items priced at S${max_price:.2f} or below."
            message += "\n\nDon't worry if you don't hear from me for a while - it just means I haven't found any matches yet. I'll keep looking!"

            keyboard = [[InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update_message(update, message, reply_markup=reply_markup)
            return MAIN_MENU
        else:
            return await handle_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in handle_set_frequency function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while setting the search frequency. Please try again later.")
        return await show_main_menu(update, context)

async def scheduled_search(context: ContextTypes.DEFAULT_TYPE):
    try:
        job = context.job
        search_term = job.data['search_term']
        max_price = job.data['max_price']

        logger.info(f"Running scheduled search for '{search_term}' with max price {max_price}")
        results, filepath = await scrape_carousell_async(search_term)

        if results:
            matching_items = [item for item in results if
                              max_price is None or float(item['price'].replace('S$', '').replace(',', '')) <= max_price]
            if matching_items:
                message = f"🔔 Alert! I found {len(matching_items)} item(s) matching your search for '{search_term}'"
                if max_price:
                    message += f" at or below S${max_price:.2f}"
                message += ":\n\n"
                for item in matching_items[:5]:
                    message += f"• {item['name']}\n  💰 Price: {item['price']}\n  🔗 Link: carousell.sg/u/{item['username']}/\n\n"
                if len(matching_items) > 5:
                    message += f"\nThere are {len(matching_items) - 5} more items. Check the full results in the CSV file."

                # Send CSV file
                if filepath:
                    await context.bot.send_message(job.chat_id, message)
                    await context.bot.send_document(job.chat_id, document=open(filepath, 'rb'),
                                                    filename=os.path.basename(filepath))
                    logger.info(f"Sent alert for {len(matching_items)} items to user {job.chat_id}")
    except Exception as e:
        logger.error(f"Error in scheduled_search function: {str(e)}", exc_info=True)

async def stop_scheduled_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info(f"User {update.effective_user.id} stopping scheduled searches")
        if 'job' in context.chat_data:
            job = context.chat_data['job']
            job.schedule_removal()
            del context.chat_data['job']
            await update_message(update, "✅ Your scheduled searches have been stopped. You won't receive any more automatic notifications.")
        else:
            await update_message(update, "You don't have any active scheduled searches. Would you like to set one up?")

        keyboard = [[InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update_message(update, "Is there anything else I can help you with?", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in stop_scheduled_search function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while stopping the scheduled search. Please try again later.")

async def view_tracked_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        tracked_items = context.user_data.get('tracked_items', [])

        if not tracked_items:
            keyboard = [[InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update_message(update, "You don't have any tracked items yet. Would you like to set a price alert?", reply_markup=reply_markup)
            return MAIN_MENU

        message = "📋 Here are your tracked items:\n\n"
        keyboard = []
        for i, item in enumerate(tracked_items):
            message += f"{i + 1}. {item['name']} - S${item['price']:.2f}\n"
            keyboard.append([InlineKeyboardButton(f"Edit {item['name']}", callback_data=f'edit_{i}')])

        keyboard.append([InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update_message(update, message, reply_markup=reply_markup)
        return VIEW_TRACKED_ITEMS
    except Exception as e:
        logger.error(f"Error in view_tracked_items function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while viewing tracked items. Please try again later.")
        return await show_main_menu(update, context)

async def handle_edit_tracked_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        if query.data == 'back_to_main':
            return await show_main_menu(update, context)

        item_index = int(query.data.split('_')[1])
        item = context.user_data['tracked_items'][item_index]

        context.user_data['editing_item'] = item_index

        await update_message(update, f"You're editing the alert for '{item['name']}' with current max price S${item['price']:.2f}.\n"
                                     "To update, enter a new item name and max price (e.g., 'iPhone 12 500'), or type 'delete' to remove this alert.")
        return EDIT_TRACKED_ITEM
    except Exception as e:
        logger.error(f"Error in handle_edit_tracked_item function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while editing the tracked item. Please try again later.")
        return await show_main_menu(update, context)

async def handle_edit_tracked_item_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_input = update.message.text.strip().lower()
        item_index = context.user_data['editing_item']

        if user_input == 'delete':
            del context.user_data['tracked_items'][item_index]
            await update_message(update, "✅ Alert deleted successfully.")
        else:
            try:
                item_name, max_price = user_input.rsplit(' ', 1)
                max_price = float(max_price)
                context.user_data['tracked_items'][item_index] = {'name': item_name, 'price': max_price}
                await update_message(update, f"✅ Alert updated: '{item_name}' with max price S${max_price:.2f}")
            except ValueError:
                await update_message(update, "❌ Invalid input. Please try again with format 'item name price' or 'delete'.")
                return EDIT_TRACKED_ITEM

        del context.user_data['editing_item']
        return await view_tracked_items(update, context)
    except Exception as e:
        logger.error(f"Error in handle_edit_tracked_item_input function: {str(e)}", exc_info=True)
        await update_message(update, "An error occurred while processing your input. Please try again later.")
        return await show_main_menu(update, context)