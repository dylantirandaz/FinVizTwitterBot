# Insider Sales Twitter Bot

This is a Twitter bot that scrapes insider sales data from FinViz and posts sales over a specified amount on Twitter.

## Installation

1. Clone the repository: git clone https://github.com/dylantirandaz/FinVizTwitterBot.git
2. Install the required libraries: pip install -r requirements.txt
3. Set up your Twitter API credentials:
- Create a new Twitter Developer account and app.
- Obtain the API key, API secret key, Access token, and Access token secret.
- Update the `config.py` file with your credentials.

## Usage

1. Run the bot: python insidersales_bot.py
2. The bot will continuously run, checking for new insider sales every hour and posting them on Twitter if found.

## Configuration

- `config.py`: Update the Twitter API credentials and other configuration settings in this file.
- `MIN_SALE_AMOUNT`: Modify this variable in `config.py` to change the minimum sale amount for posting on Twitter.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
