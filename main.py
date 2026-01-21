import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния пользователя
user_states = {}  # True = меню, False = оператор

# Список тем
TOPICS = [
    "Как стать мерчантом",
    "Статус сделки или заявки",
    "Реферальная программа",
    "P2P-торговля и Express-покупки",
    "Комиссии и лимиты",
    "Отзывы пользователей",
    "KYC и безопасность аккаунта",
    "Сотрудничество с RedWallet",
    "Техническая поддержка",
    "Перейти в приложение"
]

# Ответы (можно расширить)
ANSWERS = [
    "Ответ на тему 0: Как стать мерчантом...",
    "Ответ на тему 1: Статус сделки...",
    "Ответ на тему 2: Реферальная программа...",
    "Ответ на тему 3: P2P-торговля...",
    "Ответ на тему 4: Комиссии и лимиты...",
    "Ответ на тему 5: Отзывы пользователей...",
    "Ответ на тему 6: KYC и безопасность...",
    "Ответ на тему 7: Сотрудничество...",
    "Оператор",  # Триггер для Chatwoot
    ""           # Для перехода — не нужен текст
]

# Основное меню
def get_main_menu():
    kb = []
    for i in range(0, len(TOPICS), 2):
        row = []
        row.append(InlineKeyboardButton(text=TOPICS[i], callback_data=f"topic_{i}"))
        if i + 1 < len(TOPICS):
            row.append(InlineKeyboardButton(text=TOPICS[i + 1], callback_data=f"topic_{i + 1}"))
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Кнопка "Назад"
def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="↩ Назад к темам", callback_data="back")
    ]])


# /start и /menu
@dp.message(Command("start", "menu"))
async def show_menu(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = True
    await message.answer(
        "📋 Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_main_menu()
    )


# Обработка inline-кнопок
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    # Если в режиме оператора — блокируем меню
    if not user_states.get(user_id, True):
        await callback.answer("Сначала завершите диалог с оператором.\nНапишите /menu после.", show_alert=True)
        return

    if data.startswith("topic_"):
        idx = int(data.split("_")[1])

        if idx == 8:  # Техническая поддержка
            user_states[user_id] = False
            await callback.message.answer("Оператор")
            await callback.message.answer(
                "🔄 Соединяем с оператором...\n\n"
                "После завершения диалога напишите /menu"
            )
            await callback.message.edit_reply_markup(reply_markup=None)

        elif idx == 9:  # Перейти в приложение
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="Открыть приложение @rwapp_bot",
                    url="https://t.me/rwapp_bot?start=Тест777"   # ← здесь автоматическое сообщение
                )],
                [InlineKeyboardButton(text="↩ Назад к темам", callback_data="back")]
            ])
            await callback.message.edit_text(
                "Открываем приложение RedWallet...",
                reply_markup=kb
            )

        else:  # Обычная тема
            text = ANSWERS[idx] or f"<b>{TOPICS[idx]}</b>\n\nЗдесь будет подробный ответ."
            await callback.message.edit_text(
                text,
                reply_markup=get_back_button(),
                parse_mode="HTML"
            )

    elif data == "back":
        user_states[user_id] = True
        await callback.message.edit_text(
            "📋 Выберите интересующую тему или задайте свой вопрос:",
            reply_markup=get_main_menu()
        )

    await callback.answer()


# Обработчик любых текстовых сообщений
@dp.message()
async def any_text(message: types.Message):
    user_id = message.from_user.id

    if message.text.startswith('/'):
        return

    if user_states.get(user_id, True):
        await message.answer(
            "Используйте кнопки меню или напишите /menu.",
            reply_markup=get_main_menu()
        )
    # else: здесь можно добавить пересылку в Chatwoot, если нужно


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
