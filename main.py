import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start", "menu"))
async def cmd_start(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        # Первая строка — одна длинная кнопка
        [
            types.InlineKeyboardButton(
                text="Открыть приложение",
                url="https://t.me/rwapp_bot"
            )
        ],
        # Вторая строка — три короткие кнопки
        [
            types.InlineKeyboardButton(text="FAQ", callback_data="faq"),
            types.InlineKeyboardButton(text="Стать Мерчантом", callback_data="merchant"),
            types.InlineKeyboardButton(text="Техподдержка", callback_data="support")
        ]
    ])

    await message.answer(
        "Привет! Выбери действие:",
        reply_markup=kb
    )


@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    await callback.answer(f"Нажата кнопка: {data}", show_alert=True)


async def main():
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
