#!/bin/bash
# Script to check the running status of the NSE Automation Bot

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check if the process is running
PID=$(pgrep -f "python3 automation_bot.py")

if [ -z "$PID" ]; then
    echo "----------------------------------------"
    echo "❌ NSE Automation Bot is NOT running."
    echo "----------------------------------------"
else
    echo "----------------------------------------"
    echo "✅ NSE Automation Bot is RUNNING."
    echo "PID: $PID"
    echo "Started at: $(ps -p $PID -o lstart=)"
    echo "----------------------------------------"
    echo "Last 5 lines of bot.log:"
    tail -n 5 bot.log
fi
