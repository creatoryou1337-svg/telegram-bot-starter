import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_states = {}  # True = меню, False = оператор

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

ANSWERS = [
    "Чтобы стать мерчантом RedWallet, заполните форму...",
    "Информацию о статусе сделки...",
    "Реферальная программа...",
    "P2P-торговля...",
    """Лимиты:\n• Пополнение...""",
    "Отзывы пользователей...",
    "В RedWallet используется...",
    "Вы можете оставить предложение...",
    "Оператор",
    ""
]

def get_main_keyboard():
    buttons = []
    for i in range(0, len(TOPICS), 2):
        row = []
        row.append(InlineKeyboardButton(text=TOPICS[i], callback_data=f"topic_{i}"))
        if i + 1 < len(TOPICS):
            row.append(InlineKeyboardButton(text=TOPICS[i + 1], callback_data=f"topic_{i + 1}"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Назад к темам", callback_data="back_to_topics")]
    ])

async def show_menu(chat_id: int, message_id: int = None):
    """Отправляет или редактирует сообщение с меню"""
    text = "📋 Выберите интересующую тему или задайте свой вопрос:"
    reply_markup = get_main_keyboard()

    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
        except:
            # Если нельзя отредактировать — отправляем новое
            await bot.send_message(chat_id, text, reply_markup=reply_markup)
    else:
        await bot.send_message(chat_id, text, reply_markup=reply_markup)

@dp.message(Command("start", "menu"))
async def cmd_menu_handler(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = True
    await show_menu(message.chat.id, message.message_id)

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if not user_states.get(user_id, True):
        await callback.answer("Завершите диалог с оператором.\nЗатем напишите /menu", show_alert=True)
        return

    if data.startswith("topic_"):
        try:
            idx = int(data.split("_")[1])

            if idx == 8:  # Техподдержка
                user_states[user_id] = False
                await callback.message.answer("Оператор")
                await callback.message.answer(
                    "🔄 Соединяем с оператором...\n\nПосле завершения напишите /menu"
                )
                await callback.message.edit_reply_markup(reply_markup=None)

            elif idx == 9:  # Перейти
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Открыть приложение @rwapp_bot",
                        url="https://t.me/rwapp_bot"
                    )],
                    [InlineKeyboardButton(text="↩ Назад к темам", callback_data="back_to_topics")]
                ])
                await callback.message.edit_text(
                    "Открываем приложение RedWallet:",
                    reply_markup=kb
                )

            else:
                text = ANSWERS[idx] or f"<b>{TOPICS[idx]}</b>\n\nОтвет."
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(),
                    parse_mode="HTML"
                )

        except Exception as e:
            logging.error(e)
            await callback.answer("Ошибка")

    elif data == "back_to_topics":
        user_states[user_id] = True
        await show_menu(callback.message.chat.id, callback.message.message_id)

    await callback.answer()

@dp.message()
async def fallback(message: types.Message):
    if message.text.startswith('/'):
        return
    if user_states.get(message.from_user.id, True):
        await message.answer("Используйте меню или /menu")
    # else: Chatwoot логика

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
