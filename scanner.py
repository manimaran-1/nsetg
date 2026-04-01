import pandas as pd
import indicators
import data_loader
import concurrent.futures
import pytz
from datetime import datetime

IST = pytz.timezone('Asia/Kolkata')

def check_conditions(df, symbol):
    """
    Checks if any candle in the relevant period meets the buy criteria.
    For Daily: Checks last candle.
    For Intraday: Checks all candles from today.
    Returns a list of result dictionaries.
    """
    if df.empty or len(df) < 50: # Need enough data for indicators
        return []
        
    # Calculate Indicators
    close = df['close']
    volume = df['volume']
    
    ema5 = indicators.calculate_ema(df, 5)
    ema9 = indicators.calculate_ema(df, 9)
    ema21 = indicators.calculate_ema(df, 21)
    
    stoch_rsi_k = indicators.calculate_stoch_rsi(df, length=14, rsi_length=14, k=3, d=3)
    smi = indicators.calculate_smi(df, length=10, smooth=3)
    macd_line = indicators.calculate_macd(df, fast=12, slow=26, signal=9)
    
    results = []
    
    # Determine range to check
    # If intraday (frequency < 1d), check "today's" candles
    # If daily or above, just check the last candle
    
    # Heuristic for intraday: check if time diff between last two candles is < 1 day
    is_intraday = False
    if len(df) > 1:
        time_diff = df.index[-1] - df.index[-2]
        if time_diff < pd.Timedelta(days=1):
            is_intraday = True

    indices_to_check = []
    if is_intraday:
        # Get today's date in IST
        now_ist = datetime.now(IST)
        today_date = now_ist.date()
        
        # Check last 75 candles (heuristic to cover a day for 5m/15m)
        candidates = df.index[-75:] 
        
        # Filter for today
        today_indices = [idx for idx in candidates if idx.date() == today_date]
        
        if today_indices:
            indices_to_check = today_indices
        else:
            # If no data for "today" (e.g. run at night), use the last available date
            last_date = df.index[-1].date()
            indices_to_check = [idx for idx in candidates if idx.date() == last_date]
    else:
        # Check only the last completed candle
        indices_to_check = [df.index[-1]]
    
    for idx in indices_to_check:
        try:
            # Locate position integer for iloc equivalent
            pos = df.index.get_loc(idx)
            
            # Using .iloc[pos] to get scalar values
            c = close.iloc[pos]
            v = volume.iloc[pos]
            e5 = ema5.iloc[pos]
            e9 = ema9.iloc[pos]
            e21 = ema21.iloc[pos]
            k = stoch_rsi_k.iloc[pos]
            s = smi.iloc[pos]
            m = macd_line.iloc[pos]
            
            # Check Conditions
            if (c > e5 and
                c > e9 and
                c > e21 and
                k > 70 and
                s > 30 and
                m > 0.75):
                
                results.append({
                    'Stock Name': symbol,
                    'LTP': round(c, 2),
                    'Signal Time': idx.strftime('%d-%m-%Y %H:%M'),
                    'Volume': int(v),
                    'EMA5': round(e5, 2),
                    'EMA9': round(e9, 2),
                    'EMA21': round(e21, 2),
                    'Stoch RSI K': round(k, 2),
                    'SMI': round(s, 2),
                    'MACD': round(m, 2)
                })
        except Exception as e:
            continue
            
    return results

def scan_symbol(symbol, interval):
    """
    Helper for parallel processing.
    """
    df = data_loader.fetch_data(symbol, interval=interval)
    return check_conditions(df, symbol)

def scan_market(symbols, interval='1d', progress_callback=None):
    """
    Scans the list of symbols.
    """
    all_results = []
    total = len(symbols)
    completed = 0
    
    # Increase workers slightly since we might have more symbols now
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(scan_symbol, sym, interval): sym for sym in symbols}
        
        for future in concurrent.futures.as_completed(futures):
            res_list = future.result()
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
                
            if res_list:
                all_results.extend(res_list)
                
    return pd.DataFrame(all_results)
