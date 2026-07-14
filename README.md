# 🌤️ Forecast Bot

A Telegram bot that delivers daily weather forecasts powered by OpenWeather API.

## Features

- 📅 Hourly forecast (every 3 hours) for any city
- 🌡️ Estimated daily summary (avg temp, wind, precipitation)
- 📊 Weather charts (temperature, wind speed, precipitation)
- 📆 Forecast for a single day or date range (up to 5 days)
- 📬 Daily morning subscription — bot sends forecast automatically at 6 AM
- 🏙️ Per-user city settings

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and open main menu |
| `/city` | Change your city |

All other actions are handled through inline buttons.

## Tech Stack

- Python 3.13
- aiogram 3.x
- APScheduler
- OpenWeather API (free tier)
- matplotlib

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your_username/weather-bot
   cd weather-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your keys:
   ```
   OPENWEATHER_API_KEY=your_key_here
   BOT_TOKEN=your_bot_token_here
   ```

4. Run the bot:
   ```bash
   python bot/Telegra_bot.py
   ```

## Project Structure

```
Telegram/
├── bot/
│   ├── Telegra_bot.py        # Main bot logic
│   └── user_data.py          # User storage (JSON)
├── ingestion/
│   └── Telegram_weather_extract.py  # OpenWeather API + charts
├── charts/                   # Generated chart images
├── .env.example
└── requirements.txt
```

## Deployment

Designed to run 24/7 on a Raspberry Pi 4 via systemd.
