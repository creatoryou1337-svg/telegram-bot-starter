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

def get_main_keyboard():
    # ГЛАВНОЕ МЕНЮ как в RedWallet: 3 строки по 2 кнопки
    kb = ReplyKeyboardMarkup(
        keyboard=[
            # Первый ряд
            [
                KeyboardButton(text="Магазин 🛒"),
                KeyboardButton(text="Кабинет 🏠")
            ],
            # Второй ряд
            [
                KeyboardButton(text="FAQ !?"),
                KeyboardButton(text="Гарантии ✔️")
            ],
            # Третий ряд
            [
                KeyboardButton(text="Отзывы 📝"),
                KeyboardButton(text="Поддержка 🌟")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return kb

def get_support_keyboard():
    # Клавиатура для раздела ПОДДЕРЖКИ (ваши 9 тем)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            # 1 ряд
            [
                KeyboardButton(text="Как стать мерчантом"),
                KeyboardButton(text="Статус сделки")
            ],
            # 2 ряд
            [
                KeyboardButton(text="Реферальная программа"),
                KeyboardButton(text="P2P-торговля")
            ],
            # 3 ряд
            [
                KeyboardButton(text="Комиссии и лимиты"),
                KeyboardButton(text="Отзывы пользователей")
            ],
            # 4 ряд
            [
                KeyboardButton(text="KYC и безопасность"),
                KeyboardButton(text="Сотрудничество")
            ],
            # 5 ряд
            [
                KeyboardButton(text="Техническая поддержка")
            ],
            # 6 ряд - оператор и назад
            [
                KeyboardButton(text="Оператор"),
                KeyboardButton(text="↩ Главное меню")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return kb

@router.message(F.command == "start")
async def cmd_start(message: Message):
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

@router.message(F.command == "menu")
@router.message(F.text == "↩ Главное меню")
async def cmd_menu(message: Message):
    await message.answer(
        "Главное меню.",
        reply_markup=get_main_keyboard()
    )

# Обработчики для главного меню
@router.message(F.text == "Магазин 🛒")
async def handle_shop(message: Message):
    await message.answer("Раздел Магазин 🛒")

@router.message(F.text == "Кабинет 🏠")
async def handle_cabinet(message: Message):
    await message.answer("Раздел Кабинет 🏠")

@router.message(F.text == "FAQ !?")
async def handle_faq(message: Message):
    await message.answer("Раздел FAQ !?")

@router.message(F.text == "Гарантии ✔️")
async def handle_guarantees(message: Message):
    await message.answer("Раздел Гарантии ✔️")

@router.message(F.text == "Отзывы 📝")
async def handle_reviews(message: Message):
    # ВАЖНО: Это для кнопки ОТЗЫВЫ из главного меню
    await message.answer(
        "Создали отдельный чат с отзывами, только учтите, что писать в чат могут только те, кто хоть раз что-то купил.\n\n"
        "Чатик с отзывами"
    )

@router.message(F.text == "Поддержка 🌟")
async def handle_support(message: Message):
    # Это для кнопки ПОДДЕРЖКА из главного меню
    await message.answer(
        "Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_support_keyboard()
    )

# Обработчики для меню поддержки
@router.message(F.text == "Как стать мерчантом")
async def handle_merchant(message: Message):
    await message.answer("Информация о том, как стать мерчантом...")

@router.message(F.text == "Статус сделки")
async def handle_status(message: Message):
    await message.answer("Проверка статуса сделки или заявки...")

@router.message(F.text == "Реферальная программа")
async def handle_referral(message: Message):
    await message.answer("Информация о реферальной программе...")

@router.message(F.text == "P2P-торговля")
async def handle_p2p(message: Message):
    await message.answer("P2P-торговля и Express-покупки...")

@router.message(F.text == "Комиссии и лимиты")
async def handle_fees(message: Message):
    await message.answer("Комиссии и лимиты платформы...")

@router.message(F.text == "Отзывы пользователей")
async def handle_reviews_support(message: Message):
    # Это для кнопки "Отзывы пользователей" из меню поддержки
    await message.answer("Отзывы пользователей о сервисе...")

@router.message(F.text == "KYC и безопасность")
async def handle_kyc(message: Message):
    await message.answer("KYC и безопасность аккаунта...")

@router.message(F.text == "Сотрудничество")
async def handle_cooperation(message: Message):
    await message.answer("Сотрудничество с RedWallet...")

@router.message(F.text == "Техническая поддержка")
async def handle_tech_support(message: Message):
    await message.answer("Техническая поддержка...")

@router.message(F.text == "Оператор")
async def handle_operator(message: Message):
    await message.answer("Напишите @Operator или просто опишите проблему — подключим оператора!")

@router.message()
async def catch_all(message: Message):
    await message.answer(
        "Главное меню.",
        reply_markup=get_main_keyboard()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
