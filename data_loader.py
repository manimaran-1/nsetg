import yfinance as yf
import pandas as pd
import requests
import io
import pytz
from datetime import datetime, timedelta

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_nifty500_symbols():
    """
    Fetches the list of Nifty 500 symbols.
    """
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            return [f"{sym}.NS" for sym in df['Symbol'].tolist()]
    except Exception as e:
        print(f"Error fetching Nifty 500 list: {e}")
    
    # Fallback
    return [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS"
    ]

def get_nifty200_symbols():
    """
    Fetches Nifty 200 symbols.
    """
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            return [f"{sym}.NS" for sym in df['Symbol'].tolist()]
    except Exception as e:
        print(f"Error fetching Nifty 200 list: {e}")
    return get_nifty500_symbols()[:50]

def get_index_constituents(index_name):
    """
    Returns symbols for a specific index. 
    Ideally, this would scrape NSE, but for stability we use hardcoded major stocks or fetch if possible.
    Since we don't have a direct API for constituents of all indices, we will use a mapping approach.
    For this version, we will return Nifty 500 filtered by sector if we had sector info, 
    but yfinance doesn't give sector easily in bulk.
    
    So we will rely on fetching the CSVs from NSE archives where available.
    """
    # Map index names to their CSV URLs or equivalent
    # NSE changes these URLs often, so this is best effort.
    # A more robust way for a production app is to maintain a local database.
    
    # For now, we will return the Nifty 500 list and let the user know 
    # that specific sectoral filtering requires external data sources not easily accessible without an API key. 
    # HOWEVER, the user asked for "ALL NSE INDEXES".
    
    # Let's try to fetch specific lists if requested.
    # Common sectoral indices URLs pattern: ind_nifty[sector]list.csv
    
    slugs = {
        "Nifty Bank": "niftybank",
        "Nifty Auto": "niftyauto",
        "Nifty IT": "niftyit",
        "Nifty PSU Bank": "niftypsubank",
        "Nifty Fin Service": "niftyfinancelist", 
        "Nifty Pharma": "niftypharma",
        "Nifty FMCG": "niftyfmcg",
        "Nifty Metal": "niftymetal",
        "Nifty Media": "niftymedia",
        "Nifty Energy": "niftyenergy",
        "Nifty Realty": "niftyrealty",
        "Nifty 100": "nifty100",
        "Nifty Next 50": "niftynext50",
        "Nifty Microcap 250": "niftymicrocap250",
        "Nifty Midcap 150": "niftymidcap150",
        "Nifty Smallcap 250": "niftysmallcap250",
        "Nifty 500": "nifty500", # Redundant but safe
        "Nifty 200": "nifty200", # Redundant but safe
        "Nifty Commodities": "niftycommodities",
        "Nifty CPSE": "niftycpse",
        "Nifty Infrastructure": "niftyinfrastructure",
        "Nifty MNC": "niftymnc",
        "Nifty PSE": "niftypse",
        "Nifty Services Sector": "niftyservicesector"
    }
    
    if index_name in slugs:
        slug = slugs[index_name]
        try:
            # Try standard URL pattern
            url = f"https://archives.nseindia.com/content/indices/ind_{slug}list.csv"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
                return [f"{sym}.NS" for sym in df['Symbol'].tolist()]
        except:
            pass
            
    # Fallback: Return empty or Nifty 50
    print(f"Could not fetch constituents for {index_name}")
    return []

def get_all_indices_dict():
    """
    Returns a dictionary of Index Name -> Function/Identifier to fetch it.
    """
    return {
        "Nifty 50": "Nifty 50",
        "Nifty Next 50": "Nifty Next 50",
        "Nifty 100": "Nifty 100",
        "Nifty 200": "Nifty 200",
        "Nifty 500": "Nifty 500",
        "Nifty Microcap 250": "Nifty Microcap 250",
        "Nifty Bank": "Nifty Bank",
        "Nifty Auto": "Nifty Auto",
        "Nifty IT": "Nifty IT",
        "Nifty PSU Bank": "Nifty PSU Bank",
        "Nifty Financial Services": "Nifty Fin Service",
        "Nifty Pharma": "Nifty Pharma",
        "Nifty FMCG": "Nifty FMCG",
        "Nifty Metal": "Nifty Metal",
        "Nifty Media": "Nifty Media",
        "Nifty Energy": "Nifty Energy",
        "Nifty Realty": "Nifty Realty",
        "Nifty Commodities": "Nifty Commodities", # Might fail if no CSV
        "Nifty CPSE": "Nifty CPSE",
        "Nifty Infrastructure": "Nifty Infrastructure",
        "Nifty MNC": "Nifty MNC",
        "Nifty PSE": "Nifty PSE",
        "Nifty Services Sector": "Nifty Services Sector"
    }

def fetch_data(symbol, period='1y', interval='1d'):
    """
    Fetches historical data for a symbol.
    Converst index to Asia/Kolkata timezone.
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Adjust period based on interval to ensure enough data for indicators (e.g. EMA 200)
        # We need at least ~200 candles.
        if interval == '1m':
            period = '5d' # max allowed for 1m is 7d
        elif interval in ['2m', '5m', '15m', '30m', '60m', '90m', '1h']:
            period = '1mo' # Safe for intraday
        elif interval in ['1d', '5d', '1wk']:
            period = '1y' 
        elif interval == '1mo':
            period = '5y' # Need long history for monthly 200 EMA
            
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            # yfinance columns are Capitalized: Open, High, Low, Close, Volume
            # Standardize to lowercase for consistency
            df.columns = [c.lower() for c in df.columns]
            
            # Convert index to IST
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert(IST)
            else:
                df.index = df.index.tz_convert(IST)
                
            return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
    return pd.DataFrame()
