import pandas as pd
import numpy as np

def calculate_ema(df, length):
    """
    Calculate Exponential Moving Average.
    """
    return df['close'].ewm(span=length, adjust=False).mean()

def calculate_stoch_rsi(df, length=14, rsi_length=14, k=3, d=3):
    """
    Calculate Stochastic RSI perfectly matching Wilder's logic.
    """
    # 1. Calculate traditional RSI
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    alpha = 1 / rsi_length
    roll_up = up.ewm(alpha=alpha, adjust=False).mean()
    roll_down = down.ewm(alpha=alpha, adjust=False).mean()
    
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # 2. Calculate Stochastic of RSI
    rsi_min = rsi.rolling(window=length).min()
    rsi_max = rsi.rolling(window=length).max()
    
    # Avoid division by zero
    stoch_rsi = 100 * (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
    stoch_rsi = stoch_rsi.fillna(0)
    
    # 3. Smooth for %K
    stoch_rsi_k = stoch_rsi.rolling(window=k).mean()
    
    return stoch_rsi_k

def calculate_smi(df, length=10, smooth=3):
    """
    Calculate Stochastic Momentum Index matching Pine Script.
    """
    hh = df['high'].rolling(window=length).max()
    ll = df['low'].rolling(window=length).min()
    
    diff = hh - ll
    rdiff = df['close'] - (hh + ll) / 2
    
    avg_rdiff = rdiff.ewm(span=smooth, adjust=False).mean().ewm(span=smooth, adjust=False).mean()
    avg_diff = diff.ewm(span=smooth, adjust=False).mean().ewm(span=smooth, adjust=False).mean()
    
    smi = np.where(avg_diff != 0, 100 * avg_rdiff / (avg_diff / 2), 0)
    
    return pd.Series(smi, index=df.index)

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    Calculate MACD Line.
    """
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    return macd_line
