import asyncio
from datetime import datetime, timedelta

from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import sys
import os
import user_data as ud
from aiogram.types import CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import ingestion.Telegram_weather_extract as weather_extract
class CityForm(StatesGroup):
    waiting_for_city = State()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

class ForecastForm(StatesGroup):
    waiting_for_range_type = State()
    waiting_for_day = State()
    waiting_for_start_day = State()
    waiting_for_end_day = State()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def split_message(text: str, max_length: int = 4096) -> list[str]:
    parts = []
    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:]
    parts.append(text)
    return parts
async def send_main_menu(chat_id: int):
    un_subscribe = "🚪 Unsubscribe" if ud.user_subscribed(chat_id) else "📬 Subscribe"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{un_subscribe}", callback_data=un_subscribe)],
        [InlineKeyboardButton(text="📅 Forecast", callback_data="forecast")],
        [InlineKeyboardButton(text=" Change current city", callback_data="change_city")]
    ])
    await bot.send_message(chat_id, "🌍 Weather Assistant \n\nWhat would you like to do?", reply_markup=keyboard)

@dp.callback_query(F.data =="main_menu_keyboard")
async def main_menu_keyboard(callback: CallbackQuery):
    un_subscribe = "unsubscribe" if ud.user_subscribed(callback.message.chat.id) else "subscribe"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📬 {un_subscribe}", callback_data=f"{un_subscribe}")],
        [InlineKeyboardButton(text="📅 Forecast", callback_data="forecast")],
        [InlineKeyboardButton(text=" Change current city", callback_data="change_city")]
    ])
    await callback.message.answer("🌍 Weather Assistant \n\n What would you like to do?", reply_markup=keyboard)
    await callback.answer()
@dp.callback_query(F.data == "change_city")
async def change_city_keyboard(callback: CallbackQuery, state: FSMContext):
    await state.update_data(step="city_update")
    await state.set_state(CityForm.waiting_for_city)
    await callback.message.answer("Please enter city name: ")


@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard= InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☰ Menu", callback_data="main_menu_keyboard")],
    ])
    await message.answer(
        "🌦 **ForecastBot**\n\n"
        "Everything you need to know about the weather.\n\n"
        "• 📍 Accurate local forecasts\n"
        "• ⏰ Updates every 3 hours\n"
        "• 🌡 Temperature & feels-like\n"
        "• 🌧 Precipitation probability\n"
        "• 📊 Clean weather charts\n\n"
        "Select an action below.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(F.data =="unsubscribe_query")
async def unsubscribe_query(callback: CallbackQuery):

    if ud.user_unsubscribed(callback.message.chat.id):
        await callback.message.answer(f"Unsubscribe from {callback.message.chat.title}")
        await main_menu_keyboard(callback)
    else:
        await callback.message.answer(f"🗿 Something went wrong")


@dp.callback_query(F.data == "unsubscribe")
async def unsubscribe_handler(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes", callback_data="unsubscribe_query")],
        [InlineKeyboardButton(text="❌ No", callback_data="main_menu_keyboard")]
    ])
    await callback.message.answer("Are yo sure?", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "subscribe")
async def subscribe_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Thank you for subscribing today, please 🏙 enter city name:"
    )
    await state.update_data(step="subscribe")
    await state.set_state(CityForm.waiting_for_city)
    await callback.answer()

@dp.message(CityForm.waiting_for_city)
async def city_received(message: Message, state: FSMContext):
    city = message.text

    if not weather_extract.is_valid_city(city):
        await message.answer("❌ City not found, try again:")
        return

    data = await state.get_data()

    step = data.get("step")
    mode = data.get("mode")

    if step == "subscribe":
        ud.set_user_city(message.chat.id, city, True)
        await message.answer("🎉 Subscription activated!")
        await state.clear()
        await send_main_menu(message.chat.id)
    elif step == "city_update":
        await message.answer("✅ City updated successfully.")
        ud.set_user_city(message.chat.id, city, ud.user_subscribed(message.chat.id))
        await state.clear()
        await send_main_menu(message.chat.id)
    elif step == "city_input_manual":
        ud.set_user_city(message.chat.id, city)
        if mode == "range_selection":
            await range_handler(message,state, city)
        elif mode == "day_selection":
            await one_day_handler(message,state, city)


def create_date(start_day: datetime, end_day: datetime) -> list[str]:
    days = []

    while start_day <= end_day:
        days.append(start_day.strftime("%d.%m"))
        start_day += timedelta(days=1)

    return days


async def send_date_picker(callback: CallbackQuery,  action_prefix: str, title: str,start_day: str = None):
    today = datetime.today()
    end_day = (today + timedelta(days=5))

    if start_day is None:
        keys = create_date(today, end_day)
    else:
        date = datetime.strptime(start_day, "%d.%m")
        keys = create_date(date, end_day)
    adding = False
    inline_keyboard = []

    for key in keys:
        if start_day == key or start_day == None:
            adding = True
        if adding:
            row = [
                InlineKeyboardButton(
                    text=f"{weather_extract.get_calendar_emoji(key[0:2])}.{weather_extract.get_calendar_emoji(key[3:5])} ",
                    callback_data=f"{action_prefix}_{key}"
                )
            ]
            inline_keyboard.append(row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback.message.answer(title, reply_markup=keyboard)
    await callback.answer()



@dp.callback_query(F.data.in_({"estimated_forecast", "3hour_forecast", "charts_forecast"}))
async def forecast_type_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(forecast_type=callback.data)
    await state.set_state(ForecastForm.waiting_for_range_type)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 One day", callback_data="one_day")],
        [InlineKeyboardButton(text="📆 Range", callback_data="range")],
    ])
    await callback.message.answer("Choose period:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data =="forecast")
async def handle_forecast(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🌦️ 3 Hour forecast",callback_data="3hour_forecast")],
        [InlineKeyboardButton(text=f"🌡️Estimated forecast",callback_data="estimated_forecast")],
        [InlineKeyboardButton(text=f"📊Charts forecast",callback_data="charts_forecast")],
    ])
    await callback.message.answer("Choose the action: ",reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(ForecastForm.waiting_for_range_type, F.data == "one_day")
async def one_day_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(forecast_mode="day_selection")
    await state.set_state(ForecastForm.waiting_for_day)
    await send_date_picker(callback, "day_selection", "Choose date📅:")


@dp.callback_query(ForecastForm.waiting_for_range_type, F.data == "range")
async def range_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(forecast_mode="range_selection")
    await state.set_state(ForecastForm.waiting_for_start_day)
    await send_date_picker(callback, "range_selection", "Choose start date📅:")


@dp.callback_query(ForecastForm.waiting_for_start_day, F.data.startswith("range_selection"))
async def range_day_start_handler(callback: CallbackQuery, state: FSMContext):
    start_day = callback.data.split("_")[-1]
    await state.update_data(start_day=start_day)
    await state.set_state(ForecastForm.waiting_for_end_day)
    await send_date_picker(callback, "range_selection", "Choose end date📅:", start_day)

@dp.callback_query(ForecastForm.waiting_for_end_day, F.data.startswith("range_selection"))
async def range_day_end_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(end_day=callback.data.split("_")[-1])
    await show_city_selection(callback.message, state, callback.message.chat.id)

@dp.callback_query(ForecastForm.waiting_for_day, F.data.startswith("day_selection"))
async def range_handler_query(callback: CallbackQuery, state: FSMContext):
    await state.update_data(day=callback.data.split("_")[-1])


    await show_city_selection(callback.message, state, callback.message.chat.id)
    await callback.answer()

async def show_city_selection(message: Message, state: FSMContext, chatid: int):
    user_city = ud.get_user_city(chatid)
    text = " Unfortunately we haven't found your information in our database: "

    buttons = []
    if user_city:
        text = "Choose your city:"
        buttons.append([
            InlineKeyboardButton(
                text=f"📍 Use my city: {user_city}",
                callback_data=f"use_city_{user_city}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🏙 Enter different city",
            callback_data="enter_city_manual"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("use_city"))
async def use_my_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.replace("use_city_", "")
    data = await state.get_data()
    forecast_mode = data.get("forecast_mode")
    if forecast_mode == "day_selection":
        await one_day_handler(callback.message, state, city)
    elif forecast_mode == "range_selection":
        await range_handler(callback.message, state, city)
    await callback.answer()


@dp.callback_query(F.data == "enter_city_manual")
async def enter_city_manual(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.answer("Please 🏙 enter city name:")
    await state.update_data(step="city_input_manual")
    forecast_mode = data.get("forecast_mode")
    if forecast_mode == "range_selection":
        await state.update_data(mode="range_selection")
    elif forecast_mode == "day_selection":
        await state.update_data(mode="day_selection")
    await state.set_state(CityForm.waiting_for_city)
    await callback.answer()


async def one_day_handler(message: Message, state: FSMContext, city: str):
    data = await state.get_data()
    day = data.get("day")
    forecast_type = data.get("forecast_type")
    await state.clear()

    if forecast_type == "estimated_forecast":
        msg_text = weather_extract.create_estimated_forcast_for_certain_day(
            city, day
        )
        await message.answer(msg_text)

    elif forecast_type == "3hour_forecast":
        msg_text = weather_extract.create_3hour_summery_for_one_day(
            city, day
        )
        await message.answer(msg_text)

    elif forecast_type == "charts_forecast":
        pictures_list = weather_extract.create_chart_for_certain_day(
            city, day
        )

        caption = ["🌡️ Temperature Chart", "💨 Wind chart", "☔️ Precipitation chart"]

        for i, picture in enumerate(pictures_list):
            photo = FSInputFile(picture)
            await message.answer_photo(
                photo=photo,
                caption=f"{caption[i]} for {day}",
            )

    await send_main_menu(message.chat.id)


async def range_handler(message: Message, state: FSMContext, city: str):
    data = await state.get_data()
    day_end = data.get("end_day")
    day_start = data.get("start_day")
    forecast_type = data.get("forecast_type")

    users_city = city

    if forecast_type == "estimated_forecast":
        msg_text = weather_extract.create_estimated_forcast_more1_day(
            users_city, day_start, day_end
        )
        await message.answer(msg_text)


    elif forecast_type == "3hour_forecast":

        msg_text = weather_extract.create_3hours_for_more1_day(

            users_city, day_start, day_end

        )

        for part in split_message(msg_text):
            await message.answer(part)

    elif forecast_type == "charts_forecast":
        pictures_list = weather_extract.create_charts_for_more1_day(
            users_city, day_start, day_end
        )

        caption = ["🌡️ Temperature Chart", "💨 Wind chart", "☔️ Precipitation chart"]

        for lst in pictures_list:
            day = str(lst[0])[-9:-4]

            for i, picture in enumerate(lst[1:]):
                photo = FSInputFile(picture)
                await message.answer_photo(
                    photo=photo,
                    caption=f"{caption[i]} for {day}",
                )

    await state.clear()
    await send_main_menu(message.chat.id)

async def send_morning_forecast():
    today_day = datetime.today().strftime("%d.%m")

    subscribed = ud.subscribed_users()
    for chat_id, user_data in subscribed.items():
        city = user_data.get("city", "Tallinn")
        try:
            message = weather_extract.create_estimated_forcast_for_certain_day(city, today_day)
            await bot.send_message(chat_id, message)
            hourly = weather_extract.create_3hour_summery_for_one_day(city, today_day)
            for part in split_message(hourly):
                await bot.send_message(chat_id, part)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")


async def main():
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Tallinn"))
    scheduler.add_job(send_morning_forecast, trigger="cron", hour=19, minute=45)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())