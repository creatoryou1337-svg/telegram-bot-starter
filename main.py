import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Клавиатура с кнопкой "Один"
def get_first_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text="Один", callback_data="one")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура с кнопкой "Два" и "Назад"
def get_second_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text="Два", callback_data="two")],
        [types.InlineKeyboardButton(text="Назад ↩", callback_data="back")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Это простой пример инлайн-кнопок.",
        reply_markup=get_first_keyboard()
    )

# Обработка нажатий на inline-кнопки
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.data == "one":
        # Меняем сообщение на "Вы нажали Один" + показываем новую клавиатуру
        await callback.message.edit_text(
            "Вы нажали Один!",
            reply_markup=get_second_keyboard()
        )
    
    elif callback.data == "two":
        # Просто показываем уведомление
        await callback.answer("Вы нажали Два!", show_alert=False)
    
    elif callback.data == "back":
        # Возвращаемся к первому сообщению
        await callback.message.edit_text(
            "Привет! Это простой пример инлайн-кнопок.",
            reply_markup=get_first_keyboard()
        )
    
    # Подтверждаем нажатие
    await callback.answer()

# На любое текстовое сообщение
@dp.message()
async def any_message(message: types.Message):
    await message.answer(
        "Напишите /start для начала",
        reply_markup=get_first_keyboard()
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
