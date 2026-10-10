import os
import requests
import random
from aiogram import Bot, Dispatcher
from aiogram.types import Message
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("BLACKBOX_BOT_TOKEN")
API_KEY = os.getenv("BLACKBOX_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Легкий HTTP-сервер для проходження перевірки портів на Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

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

async def main():
    # Запускаємо вебсервер у фоновому потоці
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    # Запускаємо бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
