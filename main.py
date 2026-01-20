import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Text
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN") or "7975883175:AAGk4NQ7GSaNwR-toGQf2FhGWGc5Fe-Int8"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

THEMES = [
    "Как стать мерчантом",
    "Статус сделки или заявки",
    "P2P-торговля и Express-покупки",
    "Комиссии и лимиты",
    "Отзывы пользователей",
    "KYC и безопасность аккаунта",
    "Сотрудничество с RedWallet",
    "Техническая поддержка"
]

def get_main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    for i in range(0, len(THEMES), 2):
        row = [KeyboardButton(text=THEMES[i])]
        if i + 1 < len(THEMES):
            row.append(KeyboardButton(text=THEMES[i + 1]))
        kb.row(*row)
    kb.add(KeyboardButton(text="Связаться с оператором"))
    return kb

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Выберите интересующую тему\nили задайте свой вопрос:\n\n"
        "Также можно сразу написать оператору.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Text(equals=THEMES))
async def handle_theme(message: Message):
    theme = message.text
    text = f"<b>{theme}</b>\n\nЗдесь будет подробный ответ...\n(добавь нужный текст позже)"
    back_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    back_kb.add(KeyboardButton(text="↩ Главное меню"))
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message(Text(equals="Связаться с оператором"))
async def handle_operator(message: Message):
    await message.answer("Напишите @Operator или опишите проблему — подключим оператора!")

@dp.message(Text(equals="↩ Главное меню"))
async def back_to_main(message: Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
