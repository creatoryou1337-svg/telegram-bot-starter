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
    # Создаем клавиатуру КРУПНЫМИ кнопками внизу экрана
    # По 2 кнопки в ряд, как на скриншоте
    kb = ReplyKeyboardMarkup(
        keyboard=[
            # Первый ряд: 2 кнопки
            [
                KeyboardButton(text="Как стать мерчантом"),
                KeyboardButton(text="Статус сделки")
            ],
            # Второй ряд: 2 кнопки
            [
                KeyboardButton(text="Реферальная программа"),
                KeyboardButton(text="P2P-торговля")
            ],
            # Третий ряд: 2 кнопки
            [
                KeyboardButton(text="Комиссии и лимиты"),
                KeyboardButton(text="Отзывы пользователей")
            ],
            # Четвертый ряд: 2 кнопки
            [
                KeyboardButton(text="KYC и безопасность"),
                KeyboardButton(text="Сотрудничество")
            ],
            # Пятый ряд: 1 кнопка по центру
            [
                KeyboardButton(text="Техническая поддержка")
            ],
            # Шестой ряд: 1 кнопка оператора
            [
                KeyboardButton(text="Оператор")
            ]
        ],
        resize_keyboard=True,  # Кнопки растягиваются по ширине экрана
        one_time_keyboard=False,  # Клавиатура не скрывается
        persistent=True  # Остается всегда видимой
    )
    
    return kb

@router.message(F.command == "start")
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать!\n\n"
        "ОПЛАТА\n"
        "СЕРВИСОВ И ПР\n\n"
        "YEP",
        reply_markup=get_main_keyboard()
    )

@router.message(F.command == "menu")
@router.message(F.text == "/menu")
async def cmd_menu(message: Message):
    await message.answer(
        "Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_main_keyboard()
    )

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
async def handle_reviews(message: Message):
    await message.answer("Отзывы пользователей о сервисе...")

@router.message(F.text == "KYC и безопасность")
async def handle_kyc(message: Message):
    await message.answer("KYC и безопасность аккаунта...")

@router.message(F.text == "Сотрудничество")
async def handle_cooperation(message: Message):
    await message.answer("Сотрудничество с RedWallet...")

@router.message(F.text == "Техническая поддержка")
async def handle_support(message: Message):
    await message.answer("Техническая поддержка...")

@router.message(F.text == "Оператор")
async def handle_operator(message: Message):
    await message.answer("Напишите @Operator или просто опишите проблему — подключим оператора!")

@router.message()
async def catch_all(message: Message):
    await message.answer(
        "Используйте кнопки меню ниже или напишите /menu",
        reply_markup=get_main_keyboard()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
