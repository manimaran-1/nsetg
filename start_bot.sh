#!/bin/bash
# Script to run the NSE Automation Bot in the background using the virtual environment

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check if venv exists, if not inform the user
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment 'venv' not found."
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Run the bot in the background using nohup
echo "Starting NSE Automation Bot in the background..."
nohup python3 automation_bot.py > bot.log 2>&1 &

echo "----------------------------------------"
echo "Bot started successfully in background."
echo "PID: $!"
echo "Log file: bot.log"
echo "Use 'tail -f bot.log' to view logs."
echo "----------------------------------------"
