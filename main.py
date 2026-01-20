import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN", "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

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
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        row_width=2,
        persistent=True
    )

    # ← КЛЮЧЕВОЙ МОМЕНТ: добавляем кнопки!
    for i in range(0, len(THEMES), 2):
        row = [KeyboardButton(text=THEMES[i])]
        if i + 1 < len(THEMES):
            row.append(KeyboardButton(text=THEMES[i + 1]))
        kb.add(*row)  # ← .add() добавляет ряд кнопок

    kb.add(KeyboardButton(text="Связаться с оператором"))

    return kb

@router.message(F.command == "menu")
@router.message(F.text == "/menu")
async def cmd_menu(message: Message):
    await message.answer(
        "Выберите интересующую тему\nили задайте свой вопрос:",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text.in_(THEMES))
async def handle_theme(message: Message):
    theme = message.text
    text = f"<b>{theme}</b>\n\nЗдесь будет подробный ответ по теме...\n(пока заглушка)"
    back_kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        persistent=True
    )
    back_kb.add(KeyboardButton(text="↩ Главное меню"))
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@router.message(F.text == "Связаться с оператором")
async def handle_operator(message: Message):
    await message.answer(
        "Напишите @Operator или опишите проблему — подключим оператора!"
    )

@router.message(F.text == "↩ Главное меню")
async def back_to_main(message: Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())

@router.message()
async def catch_all(message: Message):
    await message.answer("Напишите /menu, чтобы открыть меню поддержки!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
