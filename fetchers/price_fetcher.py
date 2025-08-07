
import yfinance as yf
import pandas as pd


def get_latest_price(ticker_list):
    """Fetch the latest closing price for each ticker.

    yfinance behaves differently when a single ticker is requested – it
    returns a Series instead of a DataFrame.  The previous implementation
    assumed the result was always a DataFrame with ticker symbols as
    columns, causing single-ticker requests to return an empty result.

    This function now normalises the response so that both single and
    multiple ticker queries work consistently.
    """

    if not ticker_list:
        return {}

    data = yf.download(ticker_list, period="1d", interval="1d")
    prices = {}

    # `data["Close"]` is a Series when a single ticker is requested and a
    # DataFrame (with ticker symbols as columns) when multiple tickers are
    # requested.  Handle both cases explicitly.
    close = data["Close"] if "Close" in data else data

    if isinstance(close, pd.Series):
        prices[ticker_list[0]] = close.iloc[-1]
    else:
        for ticker in ticker_list:
            if ticker in close.columns:
                prices[ticker] = close[ticker].iloc[-1]

    return prices
