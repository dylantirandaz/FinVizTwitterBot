from requests_html import HTMLSession
import requests
from lxml import html
from lxml.cssselect import CSSSelector
from retrying import retry
import logging
import tweepy
import time
import random
from config import API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, INSIDER_SALES_URL, MIN_SALE_AMOUNT

logger = logging.getLogger(__name__)

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

def get_table(page_content):
    page_parsed = html.fromstring(page_content)
    
    headers = [
        'Ticker', 'Owner', 'Relationship', 'Date', 'Transaction', 'Cost',
        '#Shares', 'Value ($)', '#Shares Total', 'SEC Form 4'
    ]
    
    content_pane_selector = CSSSelector('div.content')
    content_pane = content_pane_selector(page_parsed)
    
    if not content_pane:
        logger.warning("Content pane not found on the page.")
        logger.debug(f"Page content: {page_content}")
        return []
    
    table = content_pane[0].xpath('.//table[contains(@class, "insider-trading-table")]')
    
    if not table:
        logger.warning("Insider trading table not found within the content pane.")
        logger.debug(f"Content pane: {html.tostring(content_pane[0])}")
        return []
    
    rows = table[0].xpath('.//tr')
    
    data_sets = []
    for row in rows[1:]:  # Skip the header row
        cols = row.xpath('.//td/text()')
        cols = [col.strip() for col in cols if col.strip()]  # Remove empty values and strip whitespace
        if len(cols) == len(headers):
            data_sets.append(dict(zip(headers, cols)))
    
    return data_sets

def get_page_with_requests_html(url):
    session = HTMLSession()
    response = session.get(url)
    response.html.render()  # This renders the JavaScript
    return response.html.html

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_insider_sales():
    try:
        page_content = get_page_with_requests_html(INSIDER_SALES_URL)
        logger.info("Insider sales page retrieved successfully.")
        logger.debug(f"Full page content: {page_content}")  # Log the full HTML content
        
        insider_sales_data = get_table(page_content)
        
        logger.info(f"Found {len(insider_sales_data)} insider sales transactions.")
        logger.info(f"Extracted data: {insider_sales_data}")
        
        sales = []
        for sale in insider_sales_data:
            if sale['Transaction'] == 'Sale':
                amount = sale['Value ($)'].replace(",", "").replace("$", "")
                try:
                    amount = float(amount)
                    if amount > MIN_SALE_AMOUNT:
                        sales.append({
                            "ticker": sale['Ticker'],
                            "owner": sale['Owner'],
                            "relation": sale['Relationship'],
                            "transaction_date": sale['Date'],
                            "transaction_type": sale['Transaction'],
                            "amount": amount,
                            "price": sale['Cost'],
                            "value": sale['Value ($)']
                        })
                except ValueError:
                    logger.warning(f"Skipping row with invalid amount: {sale}")
                    continue
        
        logger.info(f"Found {len(sales)} insider sales transactions over the minimum amount.")
        
        time.sleep(random.uniform(1, 3))
        
        return sales
    except Exception as e:
        logger.error(f"Error parsing insider sales: {str(e)}")
        return []

def post_to_twitter(sales):
    for sale in sales:
        tweet = (f"Insider Sale Alert 🚨\n"
                 f"Ticker: {sale['ticker']}\n"
                 f"Owner: {sale['owner']} ({sale['relation']})\n"
                 f"Transaction Date: {sale['transaction_date']}\n"
                 f"Amount: {sale['value']}\n"
                 f"Price: {sale['price']}")
        try:
            api.update_status(tweet)
            logger.info(f"Posted tweet: {tweet}")
        except tweepy.TweepError as e:
            logger.error(f"Error posting tweet: {e}")
