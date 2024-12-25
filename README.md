# Family Expenses Telegram Bot

## Development

### Init

1. Create `.env` file
1. Add `API_TOKEN` value with telegram bot token
1. Create empty dir called `shared`. There will be sqlite database placed.
1. Create venv and activate it: `python3 -m venv venv; source ./venv/bin/activate`
1. Install deps: `pip install -r requirements.txt`

### Run

1. Export api token: `export $(cat .env)`
1. Run `python bot.py`

## Deploy

1. Copy all files to the remote server
1. Create `.env` file
1. Add `API_TOKEN` value with telegram bot token
1. Create empty dir called `shared`. There will be sqlite database placed.
1. Run `docker-compose up -d --build`
