import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get('TELEGRAM_RIVET_CMMS_TOKEN')
if not token:
    print("TELEGRAM_RIVET_CMMS_TOKEN not found in .env")
    exit(1)

# Get bot info
response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
if response.status_code == 200:
    bot_info = response.json()
    if bot_info['ok']:
        bot = bot_info['result']
        print(f"Bot Name: {bot['first_name']}")
        print(f"Bot Username: @{bot['username']}")
        print(f"Bot ID: {bot['id']}")
        print(f"Bot URL: https://t.me/{bot['username']}")
    else:
        print(f"Error: {bot_info}")
else:
    print(f"HTTP Error: {response.status_code}")
