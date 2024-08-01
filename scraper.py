from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
from bs4 import BeautifulSoup
import logging
import csv
import os
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5

async def save_debug_info(page, prefix):
    # Save HTML
    with open(f'{prefix}_debug.html', 'w', encoding='utf-8') as f:
        f.write(await page.content())
    logger.info(f"Saved {prefix}_debug.html")

    # Save screenshot
    await page.screenshot(path=f'{prefix}_debug.png')
    logger.info(f"Saved {prefix}_debug.png")

async def scrape_carousell_async(search_term):
    logger.info(f"Searching for '{search_term}' on Carousell...")

    for attempt in range(MAX_RETRIES):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()

                try:
                    url = f"https://www.carousell.sg/search/{search_term}"
                    await page.goto(url)
                    logger.info("Page loaded.")

                    await asyncio.sleep(15)
                    logger.info("Waited for 15 seconds.")

                    async def scroll_and_load_more():
                        for i in range(5):
                            await page.evaluate("window.scrollBy(0, window.innerHeight)")
                            await asyncio.sleep(2)
                            logger.info(f"Scrolled down {i + 1} times.")

                        show_more_button = await page.query_selector('button:has-text("Show more results")')
                        if show_more_button:
                            await show_more_button.click()
                            logger.info("Clicked 'Show more results' button")
                            await asyncio.sleep(5)
                        else:
                            logger.info("'Show more results' button not found")

                    await scroll_and_load_more()

                    # Use BeautifulSoup for more flexible parsing
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    listing_cards = soup.find_all('div', {'data-testid': lambda x: x and x.startswith('listing-card-')})

                    logger.info(f"Number of listing cards found: {len(listing_cards)}")

                    if not listing_cards:
                        logger.warning("Could not find any listing elements. Saving debug info.")
                        await save_debug_info(page, 'no_listings')
                        return [], None

                    results = []
                    for i, card in enumerate(listing_cards):
                        try:
                            price = (card.select_one('p[class*="D_lf"][class*="D_lg"][class*="D_lk"][class*="D_lm"][class*="D_lq"][class*="D_lt"][class*="D_l_"]') or
                                     card.select_one('p[class*="price"]') or
                                     card.select_one('p:contains("S$")'))

                            name = (card.select_one('p[class*="D_lf"][class*="D_lg"][class*="D_lk"][class*="D_ln"][class*="D_lq"][class*="D_ls"][class*="D_lo"][class*="D_lA"]') or
                                    card.select_one('p[class*="title"]') or
                                    card.select_one('p:not(:contains("S$"))'))

                            username = card.select_one('p[data-testid="listing-card-text-seller-name"]') or card.select_one('p:contains("@")')

                            logger.info(f"Card {i + 1}: Price: {bool(price)}, Name: {bool(name)}, Username: {bool(username)}")

                            if price and name and username:
                                item = {
                                    'price': price.text.strip(),
                                    'name': name.get('title') or name.text.strip(),
                                    'username': username.text.strip()
                                }
                                results.append(item)
                                logger.info(f"Added listing: {item['name']} - {item['price']}")
                            else:
                                logger.warning(f"Incomplete data: Price: {bool(price)}, Name: {bool(name)}, Username: {bool(username)}")
                        except Exception as e:
                            logger.error(f"Error processing card {i + 1}: {str(e)}")

                    logger.info(f"Total results: {len(results)}")

                    # Save results to CSV
                    if results:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"carousell_results_{search_term.replace(' ', '_')}_{timestamp}.csv"
                        filepath = os.path.join('search_results', filename)
                        os.makedirs('search_results', exist_ok=True)

                        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                            fieldnames = ['name', 'price', 'username']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            for item in results:
                                writer.writerow(item)

                        logger.info(f"Results saved to {filepath}")
                        return results, filepath
                    else:
                        logger.info("No results found")
                        return [], None

                except PlaywrightTimeoutError:
                    logger.warning(f"Timeout occurred on attempt {attempt + 1}. Retrying...")
                    await asyncio.sleep(RETRY_DELAY)
                    continue

                except Exception as e:
                    logger.error(f"An error occurred: {str(e)}")
                    await save_debug_info(page, 'error')
                    return [], None

                finally:
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.error(f"An error occurred on attempt {attempt + 1}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Scraping failed.")
                return [], None

    # If we've reached this point, all retries failed
    return [], None