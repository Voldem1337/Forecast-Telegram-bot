import os
from operator import index
from pathlib import Path

import requests
from datetime import datetime, timedelta,timezone
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

cache = {}  # {"Tallinn": {"data": [...], "fetched_at": days_data}}
CACHE_TTL = timedelta(minutes=30)

WEATHER_EMOJI = {
    "Thunderstorm": "⛈️",
    "Drizzle": "🌦️",
    "Rain": "🌧️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Smoke": "🌫️",
    "Haze": "🌫️",
    "Dust": "🌪️",
    "Fog": "🌫️",
    "Sand": "🌪️",
    "Ash": "🌋",
    "Squall": "💨",
    "Tornado": "🌪️",
    "Clear": "☀️",
    "Clouds": "☁️",
}
HOUR_EMOJI = {
    "00": "🕛", "01": "🕐", "02": "🕑", "03": "🕒",
    "04": "🕓", "05": "🕔", "06": "🕕", "07": "🕖",
    "08": "🕗", "09": "🕘", "10": "🕙", "11": "🕚",
    "12": "🕛", "13": "🕐", "14": "🕑", "15": "🕒",
    "16": "🕓", "17": "🕔", "18": "🕕", "19": "🕖",
    "20": "🕗", "21": "🕘", "22": "🕙", "23": "🕚",
}
CALENDAR_EMOJI = {
    "01": "0️⃣1️⃣", "02": "0️⃣2️⃣", "03": "0️⃣3️⃣", "04": "0️⃣4️⃣",
    "05": "0️⃣5️⃣", "06": "0️⃣6️⃣", "07": "0️⃣7️⃣", "08": "0️⃣8️⃣",
    "09": "0️⃣9️⃣", "10": "️1️⃣0️⃣", "11": "1️⃣1️⃣", "12": "1️⃣2️⃣",
    "13": "1️⃣3️⃣", "14": "1️⃣4️⃣", "15": "1️⃣5️⃣", "16": "1️⃣6️⃣",
    "17": "1️⃣7️⃣", "18": "1️⃣8️⃣", "19": "1️⃣9️⃣", "20": "2️⃣0️⃣",
    "21": "2️⃣1️⃣", "22": "2️⃣2️⃣", "23": "2️⃣3️⃣", "24": "2️⃣4️⃣",
    "25": "2️⃣5️⃣", "26": "2️⃣6️⃣", "27": "2️⃣7️⃣", "28": "2️⃣8️⃣",
    "29": "2️⃣9️⃣", "30": "3️⃣0️⃣", "31": "3️⃣1️⃣",
}
def get_calendar_emoji(date: str) -> str:
    day = date[0:2]
    return CALENDAR_EMOJI.get(day, "📅")


Api_key = os.getenv("OPENWEATHER_API_KEY")

if Api_key == None:
    raise ValueError("OPENWEATHER_API_KEY Not Found")

def is_valid_city(city: str) -> bool:
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={Api_key}"
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False
def create_temp_chart(data: list[dict], filename: str = "temp_chart.png"):
    hours = [f"{d['hour']}:00" for d in data]
    temps = [d["temperature"] for d in data]
    feels_like = [d["feels_like"] for d in data]
    plt.figure(figsize=(10, 5))
    plt.plot(hours, temps, marker='o', label="Temperature")
    plt.plot(hours, feels_like, marker='o', label="Feels like", linestyle='--')
    plt.title(f"Forecast ({data[0]["date"]})")
    plt.xlabel("Time")
    plt.ylabel("°C", rotation=0)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()

def create_precipitation_char(data: list[dict], filename: str = "preciption_chart.png"):
    hours = [f"{d['hour']}:00" for d in data]
    probability_of_precipitation = [d["probability of precipitation"] for d in data]
    precipitation_mm = sum([d["precipitation_mm"] for d in data])
    plt.figure(figsize=(10, 5))
    plt.plot(hours, probability_of_precipitation, marker='o', label="Precipitation")
    plt.title(f"Probability of precipitation({data[0]["date"]}), total will be for the day {round(precipitation_mm,2)} mm.")
    plt.xlabel("Time")
    plt.ylabel("%", rotation=0)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)

    plt.close()


def wind_speed_char(data: list[dict], filename: str = "pop_chart.png"):
    hours = [f"{d['hour']}:00" for d in data]
    wind_speed = [d["wind_speed"] for d in data]
    wind_gust = [d["wind_gust"] for d in data]
    plt.figure(figsize=(10, 5))
    plt.plot(hours, wind_speed, marker='o', label="Wind Speed")
    plt.plot(hours, wind_gust, marker='o', label="Wind gust", linestyle='--')
    plt.title(f"Wind Speed ({data[0]["date"]})")
    plt.xlabel("Time")
    plt.ylabel("M/S", rotation=0)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()

def fetch_weather_data(city: str, api_key: str) -> dict:
    Api_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
    r = requests.get(Api_url, timeout=10)
    r.raise_for_status()
    return r.json()

def normalize_weather_data(item: dict, city: str) -> dict:
    whole_date = item["dt_txt"]
    date_part, time_part = whole_date.split(" ")
    hour = time_part.split(":")[0]
    year, month, day = date_part.split("-")

    date = f"{day}.{month}.{year[2:4]}"
    pop = item["pop"] * 100
    rain_mm = item.get("rain", {}).get("3h", 0)
    snow_mm = item.get("snow", {}).get("3h", 0)
    precipitation_mm = rain_mm + snow_mm
    precipitation_type = "Rain" if rain_mm > 0 else ("Show" if snow_mm > 0 else "No")
    return {
        "city" : city,
        "weather": item["weather"][0]["main"],
        "date": date,
        "hour": hour,
        "temperature": item["main"]["temp"],
        "feels_like": item["main"]["feels_like"],
        "humidity":item["main"]["humidity"],
        "probability of precipitation": pop,
        "precipitation_type": precipitation_type,
        "precipitation_mm" : precipitation_mm,
        "description" : item["weather"][0]["description"],
        "wind_speed": item["wind"]["speed"],
        "wind_gust": item["wind"]["gust"],
    }
def day_data_summary(data: list[dict]) -> list:
    return_array = []
    weather_today = {}
    sum_windspeed = 0
    total_precipitation = 0
    sum_temp = 0
    rain_will_start_at = []
    rain_will_end_at = []
    for item in data:
        weather_today[item["weather"]] = weather_today.get(item["weather"], 0) + 1
        precipitation_mm = item["precipitation_mm"]
        if precipitation_mm == 0 and len(rain_will_start_at) > len(rain_will_end_at):
            rain_will_end_at.append(f"{item['hour']}:00")
        elif precipitation_mm > 0 :
             rain_will_start_at.append(f"{item['hour']}:00")
        sum_windspeed += item["wind_speed"]
        total_precipitation += item["precipitation_mm"]
        sum_temp += item["temperature"]
    most_common_weather = max(weather_today, key=weather_today.get)
    return_array.append(most_common_weather)
    return_array.append(sum_temp / len(data))
    return_array.append(sum_windspeed / len(data))
    return_array.append(total_precipitation)
    return return_array



def build_summary_message(data: list[dict]):
    summary = day_data_summary(data)
    most_common_weather = summary[0]
    avg_temp = summary[1]
    avg_wind = summary[2]
    total_precipitation = summary[3]
    emoji = get_emoji(most_common_weather)

    message = (
        f"📊 Day summary for {data[0]['date']}, {data[0]['city']}: \n"
        f"🌡 Average temperature: {avg_temp:.1f}°C\n"
        f"💨 Average wind speed: {avg_wind:.1f} m/s\n"
        f"🌧 Total precipitation: {total_precipitation:.1f} mm\n"
        f"{emoji} Most common: {most_common_weather}"
    )
    return message

def hourly_summary(data: list[dict]) -> str:
    hour = data["hour"]
    weather = data["weather"]
    emoji = get_emoji(weather)
    hour_emoji = get_hour_emoji(hour)
    temp = data["temperature"]
    feels = data["feels_like"]
    humidity = data["humidity"]
    wind = data["wind_speed"]
    gust = data["wind_gust"]
    pop = data["probability of precipitation"]
    precip_mm = data["precipitation_mm"]
    precip_type = data["precipitation_type"]
    description = data["description"].capitalize()
    if precip_mm > 0:
        precip_icon = "🌧" if precip_type == "Rain" else "❄️"
        precip_line = f"{precip_icon} {precip_type}: {precip_mm:.1f}mm  |  "
    else:
        precip_line = "🌧 Rain: 0mm  |  "

    message = (
        f"{hour_emoji} {hour}:00  {emoji} {description}\n"
        f"🌡 {temp:.1f}°C  (feels like {feels:.1f}°C)\n"
        f"💧 Humidity: {humidity}%\n"
        f"{precip_line}💨 Wind: {wind:.1f} m/s (gusts {gust:.1f} m/s)\n"
        f"📊 Precipitation chance: {pop:.0f}%\n"
        f"─────────────────────────"
    )
    return message

def get_emoji(weather_main: str) -> str:
    return WEATHER_EMOJI.get(weather_main, "🌤️")

def get_hour_emoji(hour: str) -> str:
    return HOUR_EMOJI.get(hour, "🕐")

def creating_chars(data: list[dict], day_num: str) -> list[str]:
    script_dir = Path(__file__).resolve().parent
    charts_dir = script_dir.parent / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    filename_temp = charts_dir / f"temp_chart{day_num}.png"
    filename_wind_speed = charts_dir / f"wind_speed_chart{day_num}.png"
    filename_precipitation = charts_dir / f"precipitation_chart{day_num}.png"
    create_temp_chart(data, filename_temp)
    wind_speed_char(data, filename_wind_speed)
    create_precipitation_char(data, filename_precipitation)
    return [filename_temp, filename_wind_speed, filename_precipitation]


def get_forecast(city: str) -> dict[str, list]:
    now = datetime.now(timezone.utc)
    if city in cache and now - cache[city]["fetched_at"] < CACHE_TTL:
        return cache[city]["data"]

    days_data = {}
    weather_data = fetch_weather_data(city, Api_key)

    for item in weather_data["list"]:
        normalized_data = normalize_weather_data(item, city)
        day_key = normalized_data["date"][0:5]

        if day_key not in days_data:
            days_data[day_key] = []

        days_data[day_key].append(normalized_data)

    cache[city] = {
        "data": days_data,
        "fetched_at": now
    }
    return days_data

def create_estimated_forcast_for_certain_day(city : str, day: str) -> str:
    data = get_forecast(city)[day]
    return build_summary_message(data)

def create_chart_for_certain_day(city: str, day_num: str) -> list[str]:
    data = get_forecast(city)
    return creating_chars(data[day_num], day_num)

def create_estimated_forcast_more1_day(city : str, day_start: str, day_end: str) -> str:
    return_message = []
    data = get_forecast(city)
    keys = list(data.keys())
    key = day_start
    index = keys.index(day_start)
    while True:
        return_message.append(build_summary_message(data[key]))

        if key == day_end:
            break
        key = keys[index + 1]
        index += 1

    return "\n".join(return_message)

def create_charts_for_more1_day(city: str, day_start: str, day_end: str) -> list[list[str]]:
    data = get_forecast(city)
    file_paths = []
    keys = list(data.keys())
    key = day_start
    index = keys.index(day_start)
    while True:
        file_paths.append(creating_chars(data[key], key))

        if key == day_end:
            break
        key = keys[index + 1]
        index += 1

    return file_paths

def create_3hour_summery_for_one_day(city: str, day_num : str) -> str:
    data = get_forecast(city)
    if not data:
        return "No forecast data available."

    day_data = data[day_num]
    date = day_data[0]["date"]
    lines = [f"📅 {city} — {date}\n"]
    for hour_data in day_data:
        lines.append(hourly_summary(hour_data))
    lines.append(create_estimated_forcast_for_certain_day(city, day_num))
    return "\n".join(lines)

def create_3hours_for_more1_day(city: str, day_start: str,day_end: str) -> str:
    data = get_forecast(city)

    if not data:
        return "No forecast data available."

    lines = []

    keys = list(data.keys())
    key = day_start
    index = keys.index(day_start)
    while True:
        day_data = data[key]

        lines.append(f"\n📅 {city} — {key}\n")

        for hour_data in day_data:
            lines.append(hourly_summary(hour_data))
        if key == day_end:
            break
        key = keys[index + 1]
        index += 1

    return "\n".join(lines)

def main():
    city = "Tallinn"
    get_forecast(city)

if __name__ == "__main__":
    # date, temp, feels_like, weather main description, wind speed, wind gust, hour

    main()
