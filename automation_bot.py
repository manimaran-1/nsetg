import time
import os
import pytz
from datetime import datetime
import pandas as pd
import requests
import scanner
import data_loader

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Configuration via GitHub Actions Secrets / Environment Variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SCAN_UNIVERSE = os.environ.get("SCAN_UNIVERSE", "Nifty 500")
SCAN_INTERVAL = os.environ.get("SCAN_INTERVAL", "1h")
SEND_IF_EMPTY = os.environ.get("SEND_IF_EMPTY", "false").lower() == "true"

def send_telegram_message(message):
    """Sends a text message via Telegram Bot API."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Telegram Bot Token not configured. Skipping message.")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")

def send_telegram_document(file_path, caption):
    """Sends a document (CSV) via Telegram Bot API."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Telegram Bot Token not configured. Skipping document.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            files = {'document': doc}
            data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, files=files, data=data)
            return response.json()
    except Exception as e:
        print(f"Error sending document: {e}")

def run_scan():
    """Executes the stock scan and sends results to Telegram."""
    now = datetime.now(IST)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Starting Scan: {SCAN_UNIVERSE} ({SCAN_INTERVAL})")
    
    # 1. Fetch symbols based on configuration
    try:
        if SCAN_UNIVERSE == "Nifty 500":
            symbols = data_loader.get_nifty500_symbols()
        elif SCAN_UNIVERSE == "Nifty 200":
            symbols = data_loader.get_nifty200_symbols()
        elif SCAN_UNIVERSE == "Nifty 50":
            symbols = data_loader.get_nifty200_symbols()[:50]
        else:
            # Default fallback to Nifty 500
            symbols = data_loader.get_nifty500_symbols()
                
        send_telegram_message(f"🔍 *Scan Started:* {SCAN_UNIVERSE} ({SCAN_INTERVAL})\nScanning {len(symbols)} symbols...")
        
    except Exception as e:
        err_msg = f"❌ *Error fetching symbols:* {str(e)}"
        print(err_msg)
        send_telegram_message(err_msg)
        return

    # 2. Run scanner
    try:
        def progress_log(current, total):
            print(f"[{now.strftime('%H:%M:%S')}] Progress: ({current}/{total})")
            
        results_df = scanner.scan_market(symbols, interval=SCAN_INTERVAL, progress_callback=progress_log)
    except Exception as e:
        err_msg = f"❌ *Error during scan_market:* {str(e)}"
        print(err_msg)
        send_telegram_message(err_msg)
        return
    
    # 3. Handle results
    if not results_df.empty:
        # Sort by Signal Time descending
        if 'Signal Time' in results_df.columns:
            results_df = results_df.sort_values(by='Signal Time', ascending=False)
            
        filename = f"scan_results_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        results_df.to_csv(filename, index=False)
        
        caption = f"🚀 *Stock Signals Found!*\n\n"
        caption += f"📊 *Universe:* {SCAN_UNIVERSE}\n"
        caption += f"⏰ *Timeframe:* {SCAN_INTERVAL}\n"
        caption += f"✅ *Total Signals:* {len(results_df)}\n"
        caption += f"📅 *Time:* {now.strftime('%d-%m-%Y %H:%M:%S')} IST"
        
        res = send_telegram_document(filename, caption)
        print(f"Telegram response: {res}")
        
        # Clean up the temporary CSV
        if os.path.exists(filename):
            os.remove(filename)
    else:
        if SEND_IF_EMPTY:
            message = f"ℹ️ *Scan Completed*\n\n"
            message += f"📊 *Universe:* {SCAN_UNIVERSE}\n"
            message += f"⏰ *Timeframe:* {SCAN_INTERVAL}\n"
            message += f"⚠️ No stocks matched criteria at this time.\n"
            message += f"📅 *Time:* {now.strftime('%d-%m-%Y %H:%M:%S')} IST"
            res = send_telegram_message(message)
            print(f"Telegram response: {res}")

def main():
    print("========================================")
    print("   NSE Stock Scanner Automation Bot     ")
    print("========================================")
    print(f"Universe: {SCAN_UNIVERSE}")
    print(f"Interval: {SCAN_INTERVAL}")
    print(f"Timezone: IST (Asia/Kolkata)")
    print("Watching for next schedule...")
    
    last_run_hour = -1
    
    # Check if we should run a test scan immediately or if running in CI/CD (GitHub Actions)
    if os.environ.get("TEST_RUN") == "1" or os.environ.get("GITHUB_ACTIONS") == "true":
        print("Running one-off scan...")
        run_scan()
        if os.environ.get("ONCE") == "1" or os.environ.get("GITHUB_ACTIONS") == "true":
            return

    while True:
        try:
            now = datetime.now(IST)
            
            # Market Hours: 9:15 AM to 3:30 PM (15:30)
            # Weekdays only (Monday=0, Friday=4)
            is_weekday = now.weekday() < 5
            
            # Define window
            start_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
            end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            if is_weekday:
                if start_time <= now <= end_time:
                    # Check if it's a new hour and past XX:15
                    if now.hour != last_run_hour and now.minute >= 15:
                        run_scan()
                        last_run_hour = now.hour
                elif now > end_time:
                    # After market close, reset last_run_hour for tomorrow
                    if last_run_hour != -1:
                        print("Market closed. Resetting for tomorrow.")
                        last_run_hour = -1
            
            # Reset at midnight anyway
            if now.hour == 0 and now.minute == 0:
                last_run_hour = -1
                
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(10) # Pause before retrying
            
        time.sleep(30) # Poll every 30 seconds

if __name__ == "__main__":
    main()
