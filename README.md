# Carousell Search Bot

Carousell Search Bot is a Telegram bot designed to assist users with searching for items on Carousell, setting price alerts, and scheduling automatic searches. It uses web scraping and natural language processing to provide helpful information about items on Carousell.

## Features

- Answer questions about items on Carousell
- Search for items and display results
- Set price alerts for specific items
- Schedule regular automated searches
- Rate limiting to prevent spam
- User feedback system with voting buttons
- Usage statistics tracking

## Requirements

- Python 3.8+
- python-telegram-bot
- Playwright
- BeautifulSoup4
- asyncio
- Other dependencies listed in `requirements.txt`

## Setup

1. Clone this repository
2. Install dependencies:
pip install -r requirements.txt
playwright install
3. Set up environment variables:
- Create a `.env` file in the project root
- Add your Telegram bot token:
  ```
  TELEGRAM_TOKEN=your_telegram_token_here
  ```
4. Create a `search_results` directory in the project root:
   mkdir search_results
   
   ## Usage

1. Run the bot:
   python main.py

2. In Telegram, use the following commands:
- `/start` - Start the bot or return to the main menu
- `/help` - Display available commands
- `/stop` - Stop any active scheduled searches

## Configuration

- Adjust rate limiting settings in `utils.py`:
```python
RATE_LIMIT = 5  # messages
TIME_WINDOW = 60  # seconds
   
