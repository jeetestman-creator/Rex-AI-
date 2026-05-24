"""
REX Investment & Trading Skill
"""
import json
from typing import Dict, List, Optional
from datetime import datetime

from loguru import logger

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import pandas as pd
except ImportError:
    pd = None

from skills.base_skill import BaseSkill


class InvestmentSkill(BaseSkill):
    """
    Advanced Investment & Trading Skill with:
    - Stock analysis (fundamental & technical)
    - Mutual fund analysis
    - Cryptocurrency tracking
    - Forex monitoring
    - Portfolio management
    - Trading signals
    - Financial news
    """
    
    def __init__(self):
        super().__init__(
            name="investment",
            description="Financial analysis, stock tracking, and investment advisory",
            version="1.0.0",
            category="finance"
        )
        self.watchlist = []
        self.portfolio = {}
        self.alerts = []
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute investment skill"""
        try:
            action = self._detect_action(user_input)
            
            if action == "stock_info":
                result = await self.get_stock_info(user_input)
            elif action == "stock_analysis":
                result = await self.analyze_stock(user_input)
            elif action == "portfolio":
                result = await self.get_portfolio_summary()
            elif action == "crypto":
                result = await self.get_crypto_info(user_input)
            elif action == "forex":
                result = await self.get_forex_rates(user_input)
            elif action == "news":
                result = await self.get_financial_news()
            elif action == "mutual_fund":
                result = await self.analyze_mutual_fund(user_input)
            elif action == "trading_signal":
                result = await self.generate_trading_signal(user_input)
            else:
                result = await self.get_market_overview()
            
            return {
                "text": result.get("text", "Analysis complete."),
                "actions": result.get("actions", []),
                "data": result.get("data", {}),
            }
        except Exception as e:
            return {
                "text": f"Investment analysis error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _detect_action(self, text: str) -> str:
        """Detect what financial action to perform"""
        text_lower = text.lower()
        
        actions = {
            "stock_info": ["stock price", "share price", "how much is", "price of"],
            "stock_analysis": ["analyze", "analysis", "fundamental", "technical", "valuation"],
            "portfolio": ["portfolio", "my stocks", "holdings", "my investment"],
            "crypto": ["bitcoin", "ethereum", "crypto", "btc", "eth", "cryptocurrency"],
            "forex": ["forex", "exchange rate", "currency", "usd to inr", "dollar"],
            "news": ["news", "headlines", "market update", "what's happening"],
            "mutual_fund": ["mutual fund", "mf", "sip", "nav", "fund"],
            "trading_signal": ["signal", "buy", "sell", "should i", "recommend"],
        }
        
        for action, keywords in actions.items():
            if any(kw in text_lower for kw in keywords):
                return action
        
        return "market_overview"
    
    async def get_stock_info(self, text: str) -> Dict:
        """Get stock information"""
        if not yf:
            return {"text": "yfinance not installed. Run: pip install yfinance"}
        
        # Extract ticker symbol
        ticker = self._extract_ticker(text)
        if not ticker:
            return {"text": "Please specify a stock symbol (e.g., AAPL, GOOGL, RELIANCE.NS)"}
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            price = info.get('currentPrice') or info.get('regularMarketPrice', 'N/A')
            change = info.get('regularMarketChangePercent', 'N/A')
            market_cap = info.get('marketCap', 'N/A')
            
            text_response = f"""📊 **{info.get('shortName', ticker)}** ({ticker})

💰 Current Price: ${price}
📈 Change: {change}%
🏢 Market Cap: ${self._format_number(market_cap)}
📊 P/E Ratio: {info.get('trailingPE', 'N/A')}
💵 Dividend Yield: {info.get('dividendYield', 'N/A')}
📍 52W High: ${info.get('fiftyTwoWeekHigh', 'N/A')}
📍 52W Low: ${info.get('fiftyTwoWeekLow', 'N/A')}
📊 Volume: {self._format_number(info.get('volume', 'N/A'))}

📝 Summary: {info.get('longBusinessSummary', 'N/A')[:200]}..."""
            
            return {
                "text": text_response,
                "actions": ["add_to_watchlist", "set_alert", "detailed_analysis"],
                "data": {
                    "ticker": ticker,
                    "price": price,
                    "change": change,
                    "info": info,
                },
            }
        except Exception as e:
            return {"text": f"Error fetching stock info for {ticker}: {str(e)}"}
    
    async def analyze_stock(self, text: str) -> Dict:
        """Perform detailed stock analysis"""
        if not yf:
            return {"text": "yfinance not installed."}
        
        ticker = self._extract_ticker(text)
        if not ticker:
            return {"text": "Please specify a stock symbol."}
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Fundamental Analysis
            fundamental = {
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "debt_to_equity": info.get("debtToEquity"),
                "roe": info.get("returnOnEquity"),
                "profit_margin": info.get("profitMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
            }
            
            # Technical Analysis (using historical data)
            hist = stock.history(period="6mo")
            technical = {}
            
            if not hist.empty and pd:
                # Simple Moving Averages
                technical["sma_20"] = hist['Close'].rolling(20).mean().iloc[-1]
                technical["sma_50"] = hist['Close'].rolling(50).mean().iloc[-1]
                technical["sma_200"] = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else None
                
                # RSI (14-day)
                delta = hist['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                technical["rsi"] = (100 - (100 / (1 + rs))).iloc[-1]
                
                # MACD
                ema_12 = hist['Close'].ewm(span=12).mean()
                ema_26 = hist['Close'].ewm(span=26).mean()
                technical["macd"] = (ema_12 - ema_26).iloc[-1]
                
                # Current price
                current_price = hist['Close'].iloc[-1]
                
                # Signal
                signal = "NEUTRAL"
                if technical["rsi"] < 30:
                    signal = "OVERSOLD (Potential Buy)"
                elif technical["rsi"] > 70:
                    signal = "OVERBOUGHT (Potential Sell)"
                elif technical["sma_20"] and current_price > technical["sma_20"]:
                    signal = "BULLISH"
                elif technical["sma_20"] and current_price < technical["sma_20"]:
                    signal = "BEARISH"
                
                technical["signal"] = signal
            
            text_response = f"""📊 **Detailed Analysis: {ticker}**

🔍 **Fundamental Analysis:**
• P/E Ratio: {fundamental['pe_ratio']}
• Forward P/E: {fundamental['forward_pe']}
• P/B Ratio: {fundamental['pb_ratio']}
• Debt/Equity: {fundamental['debt_to_equity']}
• ROE: {fundamental['roe']}
• Profit Margin: {fundamental['profit_margin']}
• Revenue Growth: {fundamental['revenue_growth']}

📈 **Technical Analysis:**
• SMA 20: {technical.get('sma_20', 'N/A')}
• SMA 50: {technical.get('sma_50', 'N/A')}
• RSI (14): {technical.get('rsi', 'N/A'):.2f if isinstance(technical.get('rsi'), (int, float)) else 'N/A'}
• MACD: {technical.get('macd', 'N/A')}
• Signal: {technical.get('signal', 'N/A')}

⚠️ *This is not financial advice. Always do your own research.*"""
            
            return {
                "text": text_response,
                "actions": ["add_to_watchlist", "create_bot", "set_alert"],
                "data": {
                    "ticker": ticker,
                    "fundamental": fundamental,
                    "technical": technical,
                },
            }
        except Exception as e:
            return {"text": f"Analysis error: {str(e)}"}
    
    async def get_crypto_info(self, text: str) -> Dict:
        """Get cryptocurrency information"""
        if not yf:
            return {"text": "yfinance not installed."}
        
        crypto_map = {
            "bitcoin": "BTC-USD", "btc": "BTC-USD",
            "ethereum": "ETH-USD", "eth": "ETH-USD",
            "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
            "cardano": "ADA-USD", "ada": "ADA-USD",
            "solana": "SOL-USD", "sol": "SOL-USD",
        }
        
        text_lower = text.lower()
        ticker = None
        for name, symbol in crypto_map.items():
            if name in text_lower:
                ticker = symbol
                break
        
        if not ticker:
            ticker = "BTC-USD"  # Default
        
        try:
            crypto = yf.Ticker(ticker)
            info = crypto.info
            
            return {
                "text": f"""🪙 **{ticker.replace('-USD', '')}** 
💰 Price: ${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}
📈 24h Change: {info.get('regularMarketChangePercent', 'N/A')}%
📊 Market Cap: ${self._format_number(info.get('marketCap', 'N/A'))}""",
                "data": {"ticker": ticker, "info": info},
                "actions": ["add_to_watchlist", "set_alert"],
            }
        except Exception as e:
            return {"text": f"Crypto info error: {str(e)}"}
    
    async def get_market_overview(self) -> Dict:
        """Get market overview"""
        if not yf:
            return {"text": "yfinance not installed."}
        
        indices = {"^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ", 
                  "^NSEI": "NIFTY 50", "^BSESN": "SENSEX"}
        
        overview = []
        for symbol, name in indices.items():
            try:
                idx = yf.Ticker(symbol)
                info = idx.info
                price = info.get('regularMarketPrice', 'N/A')
                change = info.get('regularMarketChangePercent', 'N/A')
                emoji = "🟢" if isinstance(change, (int, float)) and change > 0 else "🔴"
                overview.append(f"{emoji} {name}: {price} ({change}%)")
            except Exception:
                overview.append(f"⚪ {name}: N/A")
        
        return {
            "text": f"📊 **Market Overview**\n\n" + "\n".join(overview),
            "actions": ["detailed_analysis", "refresh"],
            "data": {},
        }
    
    async def generate_trading_signal(self, text: str) -> Dict:
        """Generate trading signal based on technical analysis"""
        ticker = self._extract_ticker(text)
        if not ticker:
            return {"text": "Please specify a stock symbol for signal analysis."}
        
        analysis = await self.analyze_stock(text)
        
        return {
            "text": analysis["text"] + "\n\n🤖 **REX Trading Signal:** Based on the technical indicators above, consider the market conditions carefully before making any decisions.",
            "actions": ["set_alert", "backtest"],
            "data": analysis.get("data", {}),
        }
    
    def _extract_ticker(self, text: str) -> Optional[str]:
        """Extract stock ticker from text"""
        import re
        # Match common ticker patterns
        patterns = [
            r'\b([A-Z]{1,5})\b',  # US tickers
            r'\b([A-Z]+\.[A-Z]+)\b',  # International (RELIANCE.NS)
        ]
        
        # Check if text contains a known ticker format
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            for match in matches:
                if len(match) >= 2 and match not in {'THE', 'AND', 'FOR', 'WITH', 'THIS', 'THAT', 'FROM', 'REX'}:
                    return match
        
        return None
    
    def _format_number(self, num) -> str:
        """Format large numbers"""
        if not isinstance(num, (int, float)):
            return str(num)
        
        if num >= 1e12:
            return f"{num/1e12:.2f}T"
        elif num >= 1e9:
            return f"{num/1e9:.2f}B"
        elif num >= 1e6:
            return f"{num/1e6:.2f}M"
        elif num >= 1e3:
            return f"{num/1e3:.2f}K"
        return str(num)
    
    async def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        if not self.portfolio:
            return {
                "text": "📁 Your portfolio is empty. Add stocks using 'add [TICKER] [QUANTITY] [PRICE]' to your portfolio.",
                "actions": ["add_stock"],
                "data": {},
            }
        
        total_value = 0
        total_invested = 0
        holdings = []
        
        for ticker, data in self.portfolio.items():
            quantity = data.get("quantity", 0)
            avg_price = data.get("avg_price", 0)
            invested = quantity * avg_price
            total_invested += invested
            
            if yf:
                try:
                    stock = yf.Ticker(ticker)
                    current_price = stock.info.get('currentPrice', avg_price)
                    current_value = quantity * current_price
                    total_value += current_value
                    pnl = current_value - invested
                    pnl_pct = (pnl / invested * 100) if invested > 0 else 0
                    holdings.append(f"• {ticker}: {quantity} shares @ ${avg_price:.2f} → ${current_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.1f}%)")
                except Exception:
                    holdings.append(f"• {ticker}: {quantity} shares @ ${avg_price:.2f}")
        
        overall_pnl = total_value - total_invested
        overall_pct = (overall_pnl / total_invested * 100) if total_invested > 0 else 0
        
        return {
            "text": f"""📁 **Portfolio Summary**

{''.join(holdings)}

💰 Total Invested: ${total_invested:,.2f}
📊 Current Value: ${total_value:,.2f}
{'🟢' if overall_pnl >= 0 else '🔴'} Total P&L: ${overall_pnl:,.2f} ({overall_pct:.1f}%)""",
            "actions": ["add_stock", "remove_stock", "rebalance"],
            "data": {"portfolio": self.portfolio, "total_value": total_value},
        }


def register_skills(engine):
    """Register skill with REX engine"""
    skill = InvestmentSkill()
    engine.register_skill(
        name="investment",
        handler=skill.execute,
        description=skill.description
    )
