import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Токен из Render
TOKEN = os.getenv("BOT_TOKEN", "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

THEMES = [
    "Как стать мерчантом",  # Самый важный — первый
    "Статус сделки или заявки",
    "P2P-торговля и Express-покупки",
    "Реферальная программа",
    "Комиссии и лимиты",
    "Отзывы пользователей",
    "KYC и безопасность аккаунта",
    "Сотрудничество с RedWallet",
    "Техническая поддержка"
]

def get_main_keyboard():
    # Создаем список кнопок в виде списка списков
    buttons = []
    
    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(THEMES), 2):
        row = [KeyboardButton(text=THEMES[i])]
        if i + 1 < len(THEMES):
            row.append(KeyboardButton(text=THEMES[i + 1]))
        buttons.append(row)
    
    # Кнопка оператора внизу отдельно
    buttons.append([KeyboardButton(text="Оператор")])
    
    kb = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        persistent=True  # Клавиатура остаётся всегда
    )
    
    return kb

@router.message(F.command == "menu")
@router.message(F.text == "/menu")
async def cmd_menu(message: Message):
    await message.answer(
        "Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text.in_(THEMES))
async def handle_theme(message: Message):
    theme = message.text
    # Можно сделать разный текст для каждой темы позже
    text = f"<b>{theme}</b>\n\nЗдесь будет подробная информация по этой теме...\n(пока заглушка)"
    
    back_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="↩ Главное меню")]],
        resize_keyboard=True,
        persistent=True
    )
    
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@router.message(F.text == "Оператор")
async def handle_operator(message: Message):
    await message.answer(
        "Напишите @Operator или просто опишите проблему — подключим оператора!"
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
