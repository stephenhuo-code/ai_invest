
import yfinance as yf
import pandas as pd


def get_latest_price(ticker_list):
    """获取每个股票代码的最新收盘价
    
    Args:
        ticker_list: 股票代码列表
        
    Returns:
        dict: 股票代码到价格的映射
    """
    
    if not ticker_list:
        return {}
    
    try:
        # 下载股票数据
        data = yf.download(ticker_list, period="1d", interval="1d", progress=False)
        
        prices = {}
        
        # 处理单个股票的情况
        if len(ticker_list) == 1:
            ticker = ticker_list[0]
            # 单个股票时，yfinance返回的是Series
            if isinstance(data, pd.Series) and not data.empty:
                try:
                    close_price = data.iloc[-1]
                    if pd.notna(close_price):
                        prices[ticker] = close_price
                    else:
                        print(f"警告: {ticker} 的收盘价为NaN")
                except IndexError:
                    print(f"警告: {ticker} 数据索引超出范围")
            else:
                print(f"警告: {ticker} 无法获取数据")
        
        # 处理多个股票的情况
        else:
            if not data.empty and "Close" in data.columns:
                close_data = data["Close"]
                for ticker in ticker_list:
                    if ticker in close_data.columns:
                        try:
                            close_price = close_data[ticker].iloc[-1]
                            if pd.notna(close_price):
                                prices[ticker] = close_price
                            else:
                                print(f"警告: {ticker} 的收盘价为NaN")
                        except IndexError:
                            print(f"警告: {ticker} 数据索引超出范围")
                    else:
                        print(f"警告: {ticker} 不在数据列中")
            else:
                print(f"警告: 无法获取股票数据，ticker_list: {ticker_list}")
        
        return prices
        
    except Exception as e:
        print(f"获取股票价格时发生错误: {str(e)}")
        return {}
