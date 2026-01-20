import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

# ВАЖНО! Вставьте сюда ваш токен
BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()

def get_main_keyboard():
    # ГЛАВНОЕ МЕНЮ как в RedWallet: 3 строки по 2 кнопки
    kb = [
        # Первый ряд
        [
            types.KeyboardButton(text="Магазин 🛒"),
            types.KeyboardButton(text="Кабинет 🏠")
        ],
        # Второй ряд
        [
            types.KeyboardButton(text="FAQ !?"),
            types.KeyboardButton(text="Гарантии ✔️")
        ],
        # Третий ряд
        [
            types.KeyboardButton(text="Отзывы 📝"),
            types.KeyboardButton(text="Поддержка 🌟")
        ]
    ]
    return types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

def get_support_keyboard():
    # Клавиатура для раздела ПОДДЕРЖКИ (ваши 9 тем)
    kb = [
        # 1 ряд
        [
            types.KeyboardButton(text="Как стать мерчантом"),
            types.KeyboardButton(text="Статус сделки")
        ],
        # 2 ряд
        [
            types.KeyboardButton(text="Реферальная программа"),
            types.KeyboardButton(text="P2P-торговля")
        ],
        # 3 ряд
        [
            types.KeyboardButton(text="Комиссии и лимиты"),
            types.KeyboardButton(text="Отзывы пользователей")
        ],
        # 4 ряд
        [
            types.KeyboardButton(text="KYC и безопасность"),
            types.KeyboardButton(text="Сотрудничество")
        ],
        # 5 ряд
        [
            types.KeyboardButton(text="Техническая поддержка")
        ],
        # 6 ряд - оператор и назад
        [
            types.KeyboardButton(text="Оператор"),
            types.KeyboardButton(text="↩ Главное меню")
        ]
    ]
    return types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # ПРИВЕТСТВИЕ как в RedWallet
    welcome_text = (
        "Приветствуем в RedWallet!\n\n"
        "Это удобный криптокошелёк внутри Telegram, где вы можете покупать, продавать и обменивать цифровые активы — быстро, безопасно и без лишних действий.\n\n"
        "• 🔵 P2P-сделки за секунды и по прозрачному курсу\n"
        "• 🟠 Усиленная защита и продуманная анти-фрод система\n"
        "• 🟣 Инструменты как для новичков, так и для опытных трейдеров и мерчантов\n"
        "• 🟡 Честные условия работы без скрытых комиссий\n"
        "• 🟢 P2P оффлайн и мгновенные выводы (скоро)"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

# Хэндлер на команду /menu
@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer(
        "Главное меню.",
        reply_markup=get_main_keyboard()
    )

# Обработчик для кнопки "↩ Главное меню"
@dp.message(lambda message: message.text == "↩ Главное меню")
async def back_to_main(message: types.Message):
    await message.answer(
        "Главное меню.",
        reply_markup=get_main_keyboard()
    )

# Обработчик для кнопки "Отзывы 📝"
@dp.message(lambda message: message.text == "Отзывы 📝")
async def handle_reviews(message: types.Message):
    await message.answer(
        "Создали отдельный чат с отзывами, только учтите, что писать в чат могут только те, кто хоть раз что-то купил.\n\n"
        "Чатик с отзывами"
    )

# Обработчик для кнопки "Поддержка 🌟"
@dp.message(lambda message: message.text == "Поддержка 🌟")
async def handle_support(message: types.Message):
    await message.answer(
        "Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_support_keyboard()
    )

# Обработчик для кнопки "Оператор"
@dp.message(lambda message: message.text == "Оператор")
async def handle_operator(message: types.Message):
    await message.answer("Напишите @Operator или просто опишите проблему — подключим оператора!")

# Пустые обработчики для остальных кнопок (ничего не делаем)
@dp.message(lambda message: message.text in [
    "Магазин 🛒", "Кабинет 🏠", "FAQ !?", "Гарантии ✔️",
    "Как стать мерчантом", "Статус сделки", "Реферальная программа",
    "P2P-торговля", "Комиссии и лимиты", "Отзывы пользователей",
    "KYC и безопасность", "Сотрудничество", "Техническая поддержка"
])
async def handle_empty(message: types.Message):
    # Просто нажатие без ответа
    pass

# Хэндлер на остальные текстовые сообщения
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(
        "Главное меню.",
        reply_markup=get_main_keyboard()
    )

# Запуск процесса поллинга новых апдейтов
async def main():
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
