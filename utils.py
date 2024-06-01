import requests
from lxml import html
import tweepy
from retrying import retry
from config import API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, INSIDER_SALES_URL, MIN_SALE_AMOUNT
import logging
import time
import random

logger = logging.getLogger(__name__)

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

def get_table(page_content):
    page_parsed = html.fromstring(page_content)
    
    headers = [
        'Ticker', 'Owner', 'Relationship', 'Date', 'Transaction', 'Cost',
        '#Shares', 'Value ($)', '#Shares Total', 'SEC Form 4'
    ]
    rows = page_parsed.xpath('//table[@class="body-table"]//tr[contains(@class, "insider-sale-row-")]')
    
    data_sets = []
    for row in rows:
        cols = row.xpath('./td//text()')
        data_sets.append(dict(zip(headers, cols)))
    
    return data_sets

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_insider_sales():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
        }
        
        response = requests.get(INSIDER_SALES_URL, headers=headers)
        
        if response.status_code == 403:
            raise ValueError("Request blocked by the server (status code 403). Please try again later.")
        elif response.status_code != 200:
            raise ValueError(f"Request failed with status code {response.status_code}")
        
        logger.info("Insider sales page retrieved successfully.")
        
        insider_sales_data = get_table(response.content)
        
        logger.info(f"Found {len(insider_sales_data)} insider sales transactions.")
        logger.info(f"Extracted data: {insider_sales_data}")  # Add this line to log the extracted data
        
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
        
        time.sleep(random.uniform(1, 3))  # Add a random delay between requests
        
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
