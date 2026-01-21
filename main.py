import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ────────────────────────────────────────────────
# Данные для тем и ответов
# ────────────────────────────────────────────────
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
    "Перейти в приложение"          # ← НОВАЯ ТЕМА
]

# Ответы (последний — для техподдержки, новый не нужен)
ANSWERS = [
    "Чтобы стать мерчантом RedWallet, заполните форму для прохождения проверки...",
    "Информацию о статусе сделки вы можете посмотреть в приложении @rwapp_bot...",
    "Реферальная программа RedWallet позволяет получать процент...",
    "P2P-торговля позволяет покупать и продавать криптовалюту...",
    "Лимиты:\n• Пополнение и вывод от 5 USD...",
    "Отзывы пользователей о работе сервиса...",
    "В RedWallet используется усиленная система верификации...",
    "Вы можете оставить предложение о сотрудничестве...",
    "Оператор",  # Специальный триггер для Chatwoot
    ""           # Для "Перейти в приложение" ответа не нужно
]

user_states = {}  # True = меню, False = оператор

# ────────────────────────────────────────────────
# Клавиатуры
# ────────────────────────────────────────────────
def get_main_keyboard():
    buttons = []
    for i in range(0, len(TOPICS), 2):
        row = []
        row.append(types.InlineKeyboardButton(text=TOPICS[i], callback_data=f"topic_{i}"))
        if i + 1 < len(TOPICS):
            row.append(types.InlineKeyboardButton(text=TOPICS[i + 1], callback_data=f"topic_{i + 1}"))
        buttons.append(row)
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="↩ Назад к темам", callback_data="back_to_topics")]
    ])


# ────────────────────────────────────────────────
# Обработчики
# ────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = True
    await message.answer(
        "📋 Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    user_id = message.from_user.id
    if user_states.get(user_id, True):
        user_states[user_id] = True
        await message.answer(
            "📋 Выберите интересующую тему или задайте свой вопрос:",
            reply_markup=get_main_keyboard()
        )


@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if not user_states.get(user_id, True):
        await callback.answer("Закончите диалог с оператором, затем используйте /menu", show_alert=True)
        return

    if data.startswith("topic_"):
        try:
            topic_index = int(data.split("_")[1])

            if topic_index == 8:  # Техническая поддержка
                user_states[user_id] = False
                await callback.message.answer("Оператор")
                await callback.message.answer(
                    "🔄 Соединяем с оператором...\n\n"
                    "После завершения диалога напишите /menu для возврата к темам."
                )
                await callback.message.edit_reply_markup(reply_markup=None)

            elif topic_index == 9:  # ← Перейти в приложение
                # Отправляем сообщение с кнопкой-ссылкой
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="Открыть приложение @rwapp_bot",
                        url="https://t.me/rwapp_bot"
                    )]
                ])
                await callback.message.answer(
                    "Переходим в основное приложение RedWallet:",
                    reply_markup=keyboard
                )
                # Можно оставить меню или убрать — как хотите
                # await callback.message.edit_reply_markup(reply_markup=None)

            else:
                # Обычная тема
                await callback.message.edit_text(
                    f"<b>{TOPICS[topic_index]}</b>\n\n{ANSWERS[topic_index]}",
                    reply_markup=get_back_keyboard(),
                    parse_mode="HTML"
                )

        except (ValueError, IndexError):
            await callback.answer("Ошибка: тема не найдена")

    elif data == "back_to_topics":
        user_states[user_id] = True
        await callback.message.edit_text(
            "📋 Выберите интересующую тему или задайте свой вопрос:",
            reply_markup=get_main_keyboard()
        )

    await callback.answer()


@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    if message.text and message.text.startswith('/'):
        return

    if user_states.get(user_id, True):
        await message.answer(
            "Используйте меню выше или напишите /menu.\n"
            "Если нужен оператор — выберите 'Техническая поддержка'."
        )
    else:
        # Режим оператора — сообщение уходит в Chatwoot
        pass


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
