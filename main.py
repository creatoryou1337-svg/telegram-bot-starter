import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Токен берётся из переменной окружения на Render (BOT_TOKEN)
# Если хочешь протестировать локально — можно временно закомментировать и вставить хардкод
TOKEN = os.getenv("BOT_TOKEN", "7975883175:AAGk4NQ7GSaNwR-toGQf2FhGWGc5Fe-Int8")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список тем — твои 8 пунктов
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

# Функция создания клавиатуры-сетки (2 столбца + кнопка оператора)
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,         # Кнопки подстраиваются под экран
        one_time_keyboard=False,      # Не исчезает после нажатия
        row_width=2,                  # 2 кнопки в ряд
        persistent=True               # Клавиатура остаётся всегда видимой
    )
    
    # Добавляем темы по 2 в ряд
    for i in range(0, len(THEMES), 2):
        row = [KeyboardButton(text=THEMES[i])]
        if i + 1 < len(THEMES):
            row.append(KeyboardButton(text=THEMES[i + 1]))
        kb.row(*row)
    
    # Кнопка оператора внизу
    kb.add(KeyboardButton(text="Связаться с оператором"))
    
    return kb

# Команда /menu — показывает меню
@dp.message(F.command == "menu")
async def cmd_menu(message: Message):
    await message.answer(
        "Выберите интересующую тему\nили задайте свой вопрос:",
        reply_markup=get_main_keyboard()
    )

# Обработка нажатия на любую тему
@dp.message(F.text.in_(THEMES))
async def handle_theme(message: Message):
    theme = message.text
    text = f"<b>{theme}</b>\n\nЗдесь будет подробный ответ по теме...\n(пока заглушка)"
    
    back_kb = ReplyKeyboardMarkup(resize_keyboard=True, persistent=True)
    back_kb.add(KeyboardButton(text="↩ Главное меню"))
    
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# Кнопка "Связаться с оператором"
@dp.message(F.text == "Связаться с оператором")
async def handle_operator(message: Message):
    await message.answer(
        "Напишите @Operator или опишите проблему — подключим оператора!"
    )

# Кнопка "Назад"
@dp.message(F.text == "↩ Главное меню")
async def back_to_main(message: Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())

# Запуск бота (polling)
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
