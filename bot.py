logging.basicConfig(level=logging.INFO)
import logging
import os
import requests
import random
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiohttp import web

TOKEN = os.getenv("BLACKBOX_BOT_TOKEN")
API_KEY = os.getenv("BLACKBOX_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def check_number(message: Message):
    phone = message.text.strip()
    request_data = {
        "id": random.randint(1000, 9999),
        "params": {
            "phonenumber": phone,
            "api_key": API_KEY
        }
    }
    
    try:
        response = requests.get("https://blackbox.net.ua/api", params={"data": str(request_data).replace("'", '"')})
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

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # Запускаємо асинхронний вебсервер і опитування паралельно
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
