import dotenv
import os
import requests
from twilio.rest import Client

dotenv.load_dotenv()

YOUR_NUMBER = os.getenv('YOUR_PHONE')
TWILIO_NUMBER = os.getenv('TWILIO_PHONE')

STOCK = "SONY"
COMPANY_NAME = "Sony Group Corp"
CHANGE = 1


## STEP 1: Use https://www.alphavantage.co to get STOCK price
def get_stock():
    stock_url = "https://www.alphavantage.co/query?"
    stock_function = "TIME_SERIES_DAILY"
    stock_api = os.getenv('ALPHA_VANTAGE_API_KEY')
    stock_params = {'function': stock_function, 'symbol': STOCK, 'apikey': stock_api}

    res_stock = requests.get(stock_url, params=stock_params)
    res_stock.raise_for_status()
    return res_stock.json()


# Check if STOCK price increase/decreases by 5% between yesterday and the day before yesterday.
def compare_stock(stock_json):
    dailies = stock_json['Time Series (Daily)']

    opens = [value['1. open'] for (key, value) in dailies.items()][:2]
    current = float(opens[0])
    closes = [value['4. close'] for (key, value) in dailies.items()][:2]
    previous = float(closes[1])

    current_change = (current - previous) / previous * 100

    if current_change >= CHANGE:
        print(f"More than {CHANGE:.2f}% increase")
        return {'next_step': True, 'type': 'increase', 'percent': current_change}
    elif current_change <= -CHANGE:
        print(f"More than {CHANGE:.2f}% decrease")
        return {'next_step': True, 'type': 'decrease', 'percent': current_change}
    else:
        print(f"Only {current_change:.2f}% change.")
        return {'next_step': False}


## STEP 2: Use https://newsapi.org to get the first news pieces from the COMPANY_NAME.
def get_news():
    news_api = os.getenv('NEWS_API_KEY')
    news_params = {'q': COMPANY_NAME, 'apiKey': news_api}
    news_url = 'https://newsapi.org/v2/everything?'

    print("Getting news...")
    res_news = requests.get(news_url, news_params)
    res_news.raise_for_status()
    news_json = res_news.json()

    headline = [{'title': article['title'], 'description': article['description'].replace("\r\n", "")} for article in
                news_json['articles']][0]
    return headline


## STEP 3: Use https://www.twilio.com to send a message with the percentage change and article via SMS
def send_sms(next_step):
    if next_step['type'] == 'increase':
        symbol = "🔺"
    else:
        symbol = "🔻"

    message_body: str = f"""{STOCK}: {symbol} {next_step['percent']:.2f}%
Headline: {headline['title']}
Brief: {headline['description']}
    """

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    message = client.messages \
        .create(
        body=message_body,
        from_=TWILIO_NUMBER,
        to=YOUR_NUMBER
    )
    print(message.sid)


stock_stats = get_stock()
next_step = compare_stock(stock_stats)
if next_step['next_step']:
    headline = get_news()
    send_sms(next_step)
