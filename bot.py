import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
import asyncio

TOKEN = os.getenv("BLACKBOX_BOT_TOKEN")
API_KEY = os.getenv("BLACKBOX_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def check_number(message: Message):
    phone = message.text.strip()
    
    # Формуємо запит до BlackBox API v1
    request_data = {
        "id": 1000,
        "params": {
            "phonenumber": phone,
            "api_key": API_KEY
        }
    }
    
    try:
        response = requests.get(f"https://blackbox.net.ua/api?data=", params={"data": str(request_data).replace("'", '"')})
        res_json = response.json()
        
        if res_json.get("success"):
            data = res_json.get("data")
            if data:
                await message.answer(f"⚠️ Знайдено в базі:\n{data}")
            else:
                await message.answer("✅ У базі даних номер не знайдено.")
        else:
            err = res_json.get("error", {})
            await message.answer(f"Помилка API: {err.get('message', 'Невідома помилка')}")
    except Exception as e:
        await message.answer(f"Помилка з'єднання з сервером: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
