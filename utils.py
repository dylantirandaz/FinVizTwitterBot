import requests
from bs4 import BeautifulSoup
import tweepy
from retrying import retry
from config import API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, INSIDER_SALES_URL, MIN_SALE_AMOUNT

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_insider_sales():
    response = requests.get(INSIDER_SALES_URL)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find("table", class_="body-table")
    if not table:
        raise ValueError("Insider sales table not found")

    rows = table.find_all("tr")[1:]  # Skip header row
    sales = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        transaction_type = cols[4].text.strip()
        if transaction_type == 'Sale':
            amount = cols[6].text.strip().replace(",", "").replace("$", "")
            try:
                amount = float(amount)
                if amount > MIN_SALE_AMOUNT:
                    sales.append({
                        "ticker": cols[0].text.strip(),
                        "owner": cols[1].text.strip(),
                        "relation": cols[2].text.strip(),
                        "transaction_date": cols[3].text.strip(),
                        "transaction_type": transaction_type,
                        "amount": amount,
                        "price": cols[5].text.strip(),
                        "value": cols[6].text.strip()
                    })
            except ValueError:
                continue
    return sales

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
