
import yfinance as yf

def get_latest_price(ticker_list):
    data = yf.download(ticker_list, period="1d", interval="1d")
    prices = {}
    for ticker in ticker_list:
        if ticker in data["Close"]:
            prices[ticker] = data["Close"][ticker].iloc[-1]
    return prices
