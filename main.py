import asyncio
import logging
import aiohttp
import json

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

# Временное упрощение - работаем только с ботом, Chatwoot отлаживаем отдельно
CHATWOOT_ENABLED = True  # Можно отключить для тестов

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ХРАНИЛИЩА ===
user_states = {}  # True = меню, False = оператор

# === ПРОСТОЙ ВЫЗОВ CHATWOOT API ===
async def send_to_chatwoot_simple(user: types.User, message: str):
    """Прямая отправка в Chatwoot через их API для инбокса"""
    
    if not CHATWOOT_ENABLED:
        return False
    
    # URL для отправки сообщений в Telegram инбокс
    url = "https://help.redwallet.app/api/v1/accounts/1/inboxes/6/contacts"
    
    headers = {
        "Content-Type": "application/json",
        "api_access_token": "iAwyBVfycfViFrA8t5JZjd1R"
    }
    
    # Формируем данные как ожидает Chatwoot для Telegram
    data = {
        "inbox_id": 6,
        "contact": {
            "name": user.full_name or f"User_{user.id}",
            "phone_number": None,
            "email": None,
            "custom_attributes": {
                "telegram_id": str(user.id),
                "username": user.username or ""
            }
        },
        "message": {
            "content": message,
            "message_type": "incoming"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                status = resp.status
                response_text = await resp.text()
                
                logging.info(f"Chatwoot response: {status} - {response_text[:100]}")
                
                if status == 200:
                    return True
                else:
                    logging.error(f"Chatwoot API error: {status} - {response_text}")
                    return False
                    
    except Exception as e:
        logging.error(f"Error calling Chatwoot: {e}")
        return False

# === АЛЬТЕРНАТИВНЫЙ ВАРИАНТ - ТЕСТОВЫЙ ВЫЗОВ ===
async def test_chatwoot_connection():
    """Тестовый вызов для проверки доступности API"""
    
    test_urls = [
        "https://help.redwallet.app/api/v1/accounts/1/inboxes",
        "https://help.redwallet.app/api/v1/accounts/1/contacts",
        "https://help.redwallet.app/api/v1/accounts/1/profile"
    ]
    
    headers = {"api_access_token": "iAwyBVfycfViFrA8t5JZjd1R"}
    
    for url in test_urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    print(f"\nURL: {url}")
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"Response OK, keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                    else:
                        text = await resp.text()
                        print(f"Error: {text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")

# === ДАННЫЕ МЕНЮ ===
TOPICS = [
    "Как стать мерчантом",
    "Статус сделки или заявки", 
    "Реферальная программа",
    "P2P-торговля и Express-покупки",
    "Комиссии и лимиты",
    "Отзывы пользователей",
    "KYC и безопасность аккаунта",
    "Сотрудничество с RedWallet",
    "Техническая поддержка"
]

# === КЛАВИАТУРЫ ===
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

# === ОБРАБОТЧИКИ ===
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
    user_states[user_id] = True
    await message.answer(
        "📋 Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("test_chatwoot"))
async def cmd_test_chatwoot(message: types.Message):
    """Команда для тестирования подключения к Chatwoot"""
    await message.answer("🔄 Тестирую подключение к Chatwoot...")
    
    # Запускаем тест
    import asyncio as async_lib
    from io import StringIO
    import sys
    
    # Перенаправляем вывод
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    await test_chatwoot_connection()
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    await message.answer(f"Результат теста:\n```\n{output[:3000]}\n```", parse_mode="Markdown")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    if not user_states.get(user_id, True):
        await callback.answer("Закончите диалог с оператором, затем используйте /menu", show_alert=True)
        return
    
    if data.startswith("topic_"):
        topic_index = int(data.split("_")[1])
        
        if topic_index == 8:  # Техническая поддержка
            user_states[user_id] = False
            
            # Пробуем отправить в Chatwoot
            if CHATWOOT_ENABLED:
                success = await send_to_chatwoot_simple(
                    callback.from_user, 
                    f"🔴 Пользователь запросил оператора: {callback.from_user.full_name or callback.from_user.id}"
                )
                
                if success:
                    logging.info("Сообщение отправлено в Chatwoot")
                else:
                    logging.warning("Не удалось отправить в Chatwoot")
            
            await callback.message.answer(
                "🔄 Соединяем с оператором...\n\n"
                "После завершения диалога напишите /menu для возврата к темам."
            )
            
            await callback.message.edit_reply_markup(reply_markup=None)
            
        else:
            await callback.message.edit_text(
                f"<b>{TOPICS[topic_index]}</b>\n\nОтвет на тему будет здесь.",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
    
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
    
    if message.text.startswith('/'):
        return
    
    if user_states.get(user_id, True):
        await message.answer(
            "Используйте меню выше или напишите /menu для выбора темы.\n"
            "Если нужен оператор, выберите 'Техническая поддержка' в меню."
        )
    else:
        # Отправляем сообщение в Chatwoot
        if CHATWOOT_ENABLED:
            await send_to_chatwoot_simple(message.from_user, message.text)

async def main():
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Сначала протестируем подключение
    print("Тестируем подключение к Chatwoot...")
    asyncio.run(test_chatwoot_connection())
    
    # Затем запускаем бота
    asyncio.run(main())
