"""
Market Data Tool for AI Invest platform.

Fetches stock market data using yfinance and other financial APIs.
"""
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

from .base_tool import BaseTool, ToolResult, ToolStatus


class MarketDataFetcher(BaseTool):
    """Real market data fetcher using yfinance."""
    
    # Common stock symbols for reference
    POPULAR_SYMBOLS = [
        "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX",
        "AMD", "INTC", "CRM", "ORCL", "IBM", "V", "MA", "JPM", "BAC",
        "SPY", "QQQ", "DIA", "IWM"  # ETFs
    ]
    
    def __init__(self, cache_timeout: int = 300):  # 5 minutes cache
        super().__init__(
            name="market_data", 
            description="Fetch stock market data and prices using yfinance"
        )
        self.cache_timeout = cache_timeout
        self._cache = {}
        self._cache_timestamps = {}
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute market data fetching operations."""
        try:
            operation = kwargs.get("operation", "get_prices")
            
            if operation == "get_prices":
                return await self._get_current_prices(**kwargs)
            elif operation == "get_historical":
                return await self._get_historical_data(**kwargs)
            elif operation == "get_company_info":
                return await self._get_company_info(**kwargs)
            elif operation == "get_market_summary":
                return await self._get_market_summary()
            elif operation == "search_symbols":
                return await self._search_symbols(**kwargs)
            elif operation == "get_trending":
                return await self._get_trending_stocks()
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Unknown market data operation: {operation}"
                )
                
        except Exception as e:
            self.logger.error(f"Market data operation failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Market data operation failed: {str(e)}"
            )
    
    async def _get_current_prices(self, **kwargs) -> ToolResult:
        """Get current stock prices."""
        try:
            symbols = kwargs.get("symbols", [])
            if isinstance(symbols, str):
                symbols = [symbols]
            
            if not symbols:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="No symbols provided"
                )
            
            # Clean and validate symbols
            symbols = [symbol.upper().strip() for symbol in symbols if symbol.strip()]
            symbols = symbols[:20]  # Limit to 20 symbols to avoid rate limits
            
            self.logger.info(f"Fetching current prices for {len(symbols)} symbols")
            
            market_data = {}
            errors = []
            
            # Process symbols in batches to avoid overwhelming the API
            batch_size = 10
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                
                try:
                    # Check cache first
                    cache_hits = {}
                    uncached_symbols = []
                    
                    for symbol in batch:
                        cache_key = f"price_{symbol}"
                        if (cache_key in self._cache and 
                            cache_key in self._cache_timestamps and
                            (datetime.now() - self._cache_timestamps[cache_key]).seconds < self.cache_timeout):
                            cache_hits[symbol] = self._cache[cache_key]
                        else:
                            uncached_symbols.append(symbol)
                    
                    # Add cached data
                    market_data.update(cache_hits)
                    
                    if uncached_symbols:
                        # Fetch uncached data
                        batch_data = await self._fetch_batch_prices(uncached_symbols)
                        market_data.update(batch_data)
                        
                        # Update cache
                        for symbol, data in batch_data.items():
                            cache_key = f"price_{symbol}"
                            self._cache[cache_key] = data
                            self._cache_timestamps[cache_key] = datetime.now()
                    
                except Exception as e:
                    error_msg = f"Failed to fetch batch {batch}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                
                # Small delay between batches
                if i + batch_size < len(symbols):
                    await asyncio.sleep(0.1)
            
            return ToolResult(
                status=ToolStatus.SUCCESS if market_data else ToolStatus.ERROR,
                data={
                    "market_data": market_data,
                    "symbols_processed": len(market_data),
                    "symbols_requested": len(symbols),
                    "timestamp": datetime.now().isoformat(),
                    "errors": errors,
                    "cached_results": len([s for s in symbols if f"price_{s}" in cache_hits])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get current prices: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get current prices: {str(e)}"
            )
    
    async def _fetch_batch_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch prices for a batch of symbols."""
        batch_data = {}
        
        def fetch_data():
            results = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    history = ticker.history(period="1d")
                    
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                        prev_close = info.get('previousClose', history['Close'].iloc[-1])
                        
                        results[symbol] = {
                            "symbol": symbol,
                            "price": float(current_price),
                            "previous_close": float(prev_close),
                            "change": float(current_price - prev_close),
                            "change_percent": float((current_price - prev_close) / prev_close * 100) if prev_close else 0,
                            "volume": int(history['Volume'].iloc[-1]) if not history['Volume'].empty else 0,
                            "high": float(history['High'].iloc[-1]) if not history['High'].empty else float(current_price),
                            "low": float(history['Low'].iloc[-1]) if not history['Low'].empty else float(current_price),
                            "market_cap": info.get('marketCap'),
                            "pe_ratio": info.get('trailingPE'),
                            "company_name": info.get('longName', info.get('shortName', symbol)),
                            "currency": info.get('currency', 'USD')
                        }
                    else:
                        # Fallback to basic info
                        results[symbol] = {
                            "symbol": symbol,
                            "price": info.get('currentPrice', info.get('regularMarketPrice')),
                            "previous_close": info.get('previousClose'),
                            "error": "No historical data available"
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to fetch data for {symbol}: {str(e)}")
                    results[symbol] = {
                        "symbol": symbol,
                        "error": str(e)
                    }
            
            return results
        
        # Run in thread pool to avoid blocking
        batch_data = await asyncio.get_event_loop().run_in_executor(None, fetch_data)
        return batch_data
    
    async def _get_historical_data(self, **kwargs) -> ToolResult:
        """Get historical stock data."""
        try:
            symbols = kwargs.get("symbols", [])
            period = kwargs.get("period", "1mo")  # 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval = kwargs.get("interval", "1d")  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            
            if isinstance(symbols, str):
                symbols = [symbols]
            
            if not symbols:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="No symbols provided"
                )
            
            symbols = [symbol.upper().strip() for symbol in symbols[:5]]  # Limit to 5 for historical data
            
            def fetch_historical():
                results = {}
                for symbol in symbols:
                    try:
                        ticker = yf.Ticker(symbol)
                        history = ticker.history(period=period, interval=interval)
                        
                        if not history.empty:
                            # Convert to serializable format
                            history_data = []
                            for date, row in history.iterrows():
                                history_data.append({
                                    "date": date.isoformat(),
                                    "open": float(row['Open']),
                                    "high": float(row['High']),
                                    "low": float(row['Low']),
                                    "close": float(row['Close']),
                                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
                                })
                            
                            results[symbol] = {
                                "symbol": symbol,
                                "period": period,
                                "interval": interval,
                                "data_points": len(history_data),
                                "data": history_data
                            }
                        else:
                            results[symbol] = {
                                "symbol": symbol,
                                "error": "No historical data available"
                            }
                            
                    except Exception as e:
                        results[symbol] = {
                            "symbol": symbol,
                            "error": str(e)
                        }
                
                return results
            
            historical_data = await asyncio.get_event_loop().run_in_executor(None, fetch_historical)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "historical_data": historical_data,
                    "symbols_processed": len(historical_data),
                    "period": period,
                    "interval": interval,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get historical data: {str(e)}"
            )
    
    async def _get_company_info(self, **kwargs) -> ToolResult:
        """Get detailed company information."""
        try:
            symbol = kwargs.get("symbol", "").upper().strip()
            if not symbol:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Symbol parameter is required"
                )
            
            def fetch_info():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # Extract key information
                    company_info = {
                        "symbol": symbol,
                        "company_name": info.get('longName', info.get('shortName', symbol)),
                        "sector": info.get('sector'),
                        "industry": info.get('industry'),
                        "business_summary": info.get('longBusinessSummary'),
                        "market_cap": info.get('marketCap'),
                        "enterprise_value": info.get('enterpriseValue'),
                        "pe_ratio": info.get('trailingPE'),
                        "forward_pe": info.get('forwardPE'),
                        "peg_ratio": info.get('pegRatio'),
                        "price_to_book": info.get('priceToBook'),
                        "dividend_yield": info.get('dividendYield'),
                        "beta": info.get('beta'),
                        "52_week_high": info.get('fiftyTwoWeekHigh'),
                        "52_week_low": info.get('fiftyTwoWeekLow'),
                        "employees": info.get('fullTimeEmployees'),
                        "website": info.get('website'),
                        "country": info.get('country'),
                        "city": info.get('city'),
                        "phone": info.get('phone'),
                        "recommendation_key": info.get('recommendationKey'),
                        "target_high_price": info.get('targetHighPrice'),
                        "target_low_price": info.get('targetLowPrice'),
                        "target_mean_price": info.get('targetMeanPrice')
                    }
                    
                    return company_info
                    
                except Exception as e:
                    return {"symbol": symbol, "error": str(e)}
            
            company_info = await asyncio.get_event_loop().run_in_executor(None, fetch_info)
            
            if "error" in company_info:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Failed to get company info for {symbol}: {company_info['error']}"
                )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=company_info
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get company info: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get company info: {str(e)}"
            )
    
    async def _get_market_summary(self) -> ToolResult:
        """Get market summary with major indices."""
        try:
            major_indices = ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"]  # S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX
            
            prices_result = await self._get_current_prices(symbols=major_indices)
            
            if prices_result.is_success:
                market_summary = {
                    "timestamp": datetime.now().isoformat(),
                    "indices": prices_result.data["market_data"],
                    "market_status": self._get_market_status()
                }
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=market_summary
                )
            else:
                return prices_result
                
        except Exception as e:
            self.logger.error(f"Failed to get market summary: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get market summary: {str(e)}"
            )
    
    async def _search_symbols(self, **kwargs) -> ToolResult:
        """Search for stock symbols (basic implementation)."""
        try:
            query = kwargs.get("query", "").lower().strip()
            if not query:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Query parameter is required"
                )
            
            # Simple search in popular symbols (in real implementation, you'd use a proper search API)
            matches = []
            for symbol in self.POPULAR_SYMBOLS:
                if query in symbol.lower():
                    matches.append(symbol)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "query": query,
                    "matches": matches,
                    "note": "This is a basic search in popular symbols. For comprehensive search, integrate with a proper symbol search API."
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to search symbols: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to search symbols: {str(e)}"
            )
    
    async def _get_trending_stocks(self) -> ToolResult:
        """Get trending stocks (simplified implementation)."""
        try:
            # In a real implementation, you'd use APIs like Yahoo Finance trending or similar
            # For now, return popular tech stocks as a placeholder
            trending_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN"]
            
            prices_result = await self._get_current_prices(symbols=trending_symbols)
            
            if prices_result.is_success:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "trending_stocks": prices_result.data["market_data"],
                        "timestamp": datetime.now().isoformat(),
                        "note": "This is a simplified trending list. For real trending data, integrate with proper trending APIs."
                    }
                )
            else:
                return prices_result
                
        except Exception as e:
            self.logger.error(f"Failed to get trending stocks: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get trending stocks: {str(e)}"
            )
    
    def _get_market_status(self) -> str:
        """Get current market status (simplified)."""
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        
        # Simplified market hours (US Eastern Time approximation)
        if weekday >= 5:  # Weekend
            return "closed_weekend"
        elif 9 <= hour < 16:  # Roughly market hours
            return "open"
        elif hour < 9:
            return "pre_market"
        else:
            return "after_hours"
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for this tool."""
        return {
            "parameters": {
                "operation": {
                    "type": "string",
                    "enum": ["get_prices", "get_historical", "get_company_info", "get_market_summary", "search_symbols", "get_trending"],
                    "description": "Market data operation to perform"
                },
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Stock symbols to fetch data for"
                },
                "symbol": {
                    "type": "string",
                    "description": "Single stock symbol for company info"
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                    "description": "Historical data period",
                    "default": "1mo"
                },
                "interval": {
                    "type": "string",
                    "enum": ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"],
                    "description": "Historical data interval",
                    "default": "1d"
                },
                "query": {
                    "type": "string",
                    "description": "Search query for symbol search"
                }
            },
            "required": ["operation"]
        }