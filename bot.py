import os
import re
import json
import random
import asyncio
import logging

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("blackbox-bot")

TOKEN = os.getenv("BLACKBOX_BOT_TOKEN")
API_KEY = os.getenv("BLACKBOX_API_KEY")
API_URL = "https://blackbox.net.ua/api"

if not TOKEN:
    raise SystemExit("Не задано змінну BLACKBOX_BOT_TOKEN")
if not API_KEY:
    log.warning("Не задано змінну BLACKBOX_API_KEY, запити до API не працюватимуть")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def normalize_phone(raw: str):
    """Залишає лише цифри і приводить до формату 0XXXXXXXXX, як вимагає API BlackBox. Повертає None, якщо номер не схожий на український."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("380"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("80"):
        digits = digits[1:]
    elif len(digits) == 9:
        digits = "0" + digits
    if len(digits) == 10 and digits.startswith("0"):
        return digits
    return None


async def query_blackbox(phone: str) -> dict:
    """Один запит до BlackBox API. Якщо формат запиту треба змінити, міняйте лише цю функцію."""
    payload = {
        "id": random.randint(1000, 9999),
        "params": {
            "phonenumber": phone,
            "api_key": API_KEY,
        },
    }
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(API_URL, params={"data": json.dumps(payload)}) as resp:
            text = await resp.text()
            log.info("BlackBox HTTP %s: %s", resp.status, text[:500])
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"success": False, "error": {"message": f"Некоректна відповідь API (HTTP {resp.status})"}}


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привіт! Надішліть номер телефону покупця, наприклад 0671234567, "
        "і я перевірю його в базі BlackBox."
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Просто надішліть номер телефону у будь-якому форматі: 0671234567 або +380671234567.")


@dp.message()
async def check_number(message: Message):
    if not message.text:
        await message.answer("Надішліть номер телефону текстом.")
        return

    phone = normalize_phone(message.text)
    if not phone:
        await message.answer("Не схоже на український номер. Приклад: 0671234567 або +380671234567.")
        return

    log.info("Перевірка номера %s від користувача %s", phone, message.from_user.id if message.from_user else "?")

    try:
        result = await query_blackbox(phone)
    except asyncio.TimeoutError:
        await message.answer("BlackBox не відповів вчасно. Спробуйте ще раз за хвилину.")
        return
    except Exception as e:
        log.exception("Помилка запиту до BlackBox")
        await message.answer(f"Помилка з'єднання з BlackBox: {e}")
        return

    if result.get("success"):
        data = result.get("data")
        left = result.get("count_query")
        footer = f"\n\nЗапитів залишилось: {left}" if left is not None else ""
        if data:
            await message.answer(f"⚠️ Номер {phone} знайдено в базі:\n{json.dumps(data, ensure_ascii=False, indent=2)}{footer}")
        else:
            await message.answer(f"✅ Номер {phone} у базі не знайдено.{footer}")
    else:
        err = result.get("error") or {}
        await message.answer(f"Помилка API: {err.get('message', 'невідома помилка')} (код {err.get('code', '-')})")


# Простий вебсервер, щоб Render бачив відкритий порт
async def handle_ping(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info("Вебсервер слухає порт %s", port)


async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
