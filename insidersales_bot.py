import time
import logging
from utils import get_insider_sales, post_to_twitter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def main():
    while True:
        try:
            sales = get_insider_sales()
            if sales:
                post_to_twitter(sales)
            else:
                logger.info("No sales over the minimum amount found.")
            time.sleep(3600)  # Wait 1hr before next
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            time.sleep(1800)  # Wait 30 b4 retry

if __name__ == "__main__":
    main()
