import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start", "menu"))
async def show_main_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        # Две кнопки в одну линию — маленькие/средние, рядом
        [
            types.InlineKeyboardButton(
                text="Открыть приложение",
                url="https://t.me/rwapp_bot"
            ),
            types.InlineKeyboardButton(
                text="Стать Мерчантом",
                callback_data="merchant"
            )
        ]
    ])

    await message.answer(
        """Приветствуем в RedWallet!
Это удобный криптокошелёк внутри Telegram, где вы можете покупать, продавать и обменивать цифровые активы — быстро, безопасно и без лишних действий.
⚡️ P2P-сделки за секунды и по прозрачному курсу
🔒 Усиленная защита и продуманная анти-фрод система
💼 Инструменты как для новичков, так и для опытных трейдеров и мерчантов
💰 Честные условия работы без скрытых комиссий
🏦 P2P оффлайн и мгновенные выводы (скоро)""",
        reply_markup=kb
    )


@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data

    if data == "merchant":
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Открыть @redwallet_help_bot",
                    url="https://t.me/redwallet_help_bot"
                )
            ],
            [
                types.InlineKeyboardButton(text="↩ Назад", callback_data="back")
            ]
        ])

        await callback.message.edit_text(
            "Хотите стать мерчантом?\n"
            "Перейдите в бот поддержки, напишите «Мерчант», чтобы получить инструкции и подать заявку.",
            reply_markup=kb
        )

    elif data == "back":
        await show_main_menu(callback.message)

    await callback.answer()


async def main():
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
