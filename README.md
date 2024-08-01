Carousell Search Bot
Carousell Search Bot is a Telegram bot designed to assist users with searching for items on Carousell, setting price alerts, and scheduling automatic searches. It uses web scraping and natural language processing to provide helpful information about items on Carousell.
Features

Answer questions about items on Carousell
Search for items and display results
Set price alerts for specific items
Schedule regular automated searches
Rate limiting to prevent spam
User feedback system with voting buttons
Usage statistics tracking

Requirements

Python 3.8+
python-telegram-bot
Playwright
BeautifulSoup4
asyncio
Other dependencies listed in requirements.txt

Setup

Clone this repository
Install dependencies:
Copypip install -r requirements.txt
playwright install

Set up environment variables:

Create a .env file in the project root
Add your Telegram bot token:
CopyTELEGRAM_TOKEN=your_telegram_token_here



Create a search_results directory in the project root:
Copymkdir search_results


Usage

Run the bot:
Copypython main.py

In Telegram, use the following commands:

/start - Start the bot or return to the main menu
/help - Display available commands
/stop - Stop any active scheduled searches



Configuration

Adjust rate limiting settings in utils.py:
pythonCopyRATE_LIMIT = 5  # messages
TIME_WINDOW = 60  # seconds
