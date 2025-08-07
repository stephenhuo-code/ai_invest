import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fetchers import price_fetcher


def test_get_latest_price_single_ticker(monkeypatch):
    """Ensure a single-ticker query returns a price."""
    def fake_download(tickers, period="1d", interval="1d"):
        # Mimic yfinance's return for a single ticker: a DataFrame with a
        # "Close" column containing a Series.
        return pd.DataFrame({"Close": [123.45]})

    monkeypatch.setattr(price_fetcher.yf, "download", fake_download)

    result = price_fetcher.get_latest_price(["AAPL"])
    assert result == {"AAPL": 123.45}
