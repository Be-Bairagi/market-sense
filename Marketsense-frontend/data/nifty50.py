# NIFTY 50 Constituents Metadata (mirrored from backend)
NIFTY_50_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Technology"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Financial Services"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Financial Services"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "Technology"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "Consumer Goods"},
    {"symbol": "ITC.NS", "name": "ITC", "sector": "Consumer Goods"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Financial Services"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecommunication"},
    {"symbol": "LTIM.NS", "name": "LTIMindtree", "sector": "Technology"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Financial Services"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Construction"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "Financial Services"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "Consumer Goods"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "sector": "Automobile"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical", "sector": "Healthcare"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer Goods"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "sector": "Construction"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "Financial Services"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Metals"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel", "sector": "Metals"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries", "sector": "Metals"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "sector": "Metals"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp", "sector": "Energy"},
    {"symbol": "NTPC.NS", "name": "NTPC", "sector": "Energy"},
    {"symbol": "ONGC.NS", "name": "ONGC", "sector": "Energy"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "Automobile"},
]

# Quick lookup: symbol -> name
NIFTY_50_MAP = {s["symbol"]: s["name"] for s in NIFTY_50_STOCKS}

# Just the symbols list
NIFTY_50_SYMBOLS = [s["symbol"] for s in NIFTY_50_STOCKS]
