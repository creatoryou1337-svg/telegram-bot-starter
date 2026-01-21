import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("test"))
async def test_grid(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        # 1-я строка: одна длинная кнопка
        [
            InlineKeyboardButton(
                text="Открыть приложение",
                url="https://t.me/rwapp_bot"
            )
        ],
        # 2-я строка: три короткие кнопки
        [
            InlineKeyboardButton(text="FAQ", callback_data="faq"),
            InlineKeyboardButton(text="Стать Мерчантом", callback_data="merchant"),
            InlineKeyboardButton(text="Техподдержка", callback_data="support")
        ]
    ])

    await message.answer("Тестовая сетка:", reply_markup=kb)


@dp.callback_query()
async def handle_buttons(callback: types.CallbackQuery):
    await callback.answer(f"Нажата: {callback.data}", show_alert=True)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
