import asyncio
import logging
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

# === ВАШИ НАСТРОЙКИ CHATWOOT ===
CHATWOOT_API_URL = "https://help.redwallet.app"
CHATWOOT_API_TOKEN = "iAwyBVfycfViFrA8t5JZjd1R"
CHATWOOT_ACCOUNT_ID = "1"
CHATWOOT_INBOX_ID = "6"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ХРАНИЛИЩА ===
user_states = {}  # True = меню, False = оператор
user_conversations = {}  # {user_id: conversation_id}
user_contacts = {}  # {user_id: contact_id}

# === CHATWOOT API ===
async def get_or_create_chatwoot_contact(user: types.User):
    """Создаем или получаем контакт в Chatwoot"""
    user_id = user.id
    
    # Проверяем кэш
    if user_id in user_contacts:
        return user_contacts[user_id]
    
    # Создаем новый контакт
    url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    contact_data = {
        "inbox_id": CHATWOOT_INBOX_ID,
        "name": user.full_name or f"User_{user.id}",
        "phone_number": None,
        "email": None,
        "custom_attributes": {
            "telegram_id": str(user.id),
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or ""
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=contact_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    contact_id = data["payload"]["contact"]["id"]
                    user_contacts[user_id] = contact_id
                    logging.info(f"Created Chatwoot contact {contact_id} for user {user_id}")
                    return contact_id
                else:
                    error_text = await resp.text()
                    logging.error(f"Failed to create contact: {resp.status} - {error_text}")
                    return None
    except Exception as e:
        logging.error(f"Error creating Chatwoot contact: {e}")
        return None

async def create_chatwoot_conversation(contact_id, user_id):
    """Создаем диалог в Chatwoot"""
    url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    conv_data = {
        "inbox_id": CHATWOOT_INBOX_ID,
        "contact_id": contact_id,
        "status": "open"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=conv_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    conversation_id = data["id"]
                    user_conversations[user_id] = conversation_id
                    logging.info(f"Created Chatwoot conversation {conversation_id} for user {user_id}")
                    return conversation_id
                else:
                    error_text = await resp.text()
                    logging.error(f"Failed to create conversation: {resp.status} - {error_text}")
                    return None
    except Exception as e:
        logging.error(f"Error creating conversation: {e}")
        return None

async def send_message_to_chatwoot(user_id, message_text):
    """Отправляем сообщение пользователя в Chatwoot"""
    if user_id not in user_conversations:
        logging.error(f"No conversation for user {user_id}")
        return False
    
    conversation_id = user_conversations[user_id]
    url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    message_data = {
        "content": message_text,
        "message_type": "incoming",
        "private": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=message_data) as resp:
                if resp.status == 200:
                    logging.info(f"Message sent to Chatwoot: {message_text[:50]}...")
                    return True
                else:
                    error_text = await resp.text()
                    logging.error(f"Failed to send to Chatwoot: {resp.status} - {error_text}")
                    return False
    except Exception as e:
        logging.error(f"Error sending to Chatwoot: {e}")
        return False

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

ANSWERS = [
    # ... ваши 9 ответов ...
    "Оператор"  # последний ответ
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
    
    # Создаем контакт в Chatwoot
    contact_id = await get_or_create_chatwoot_contact(message.from_user)
    
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
        topic_index = int(data.split("_")[1])
        
        if topic_index == 8:  # Техническая поддержка
            user_states[user_id] = False
            
            # 1. Получаем или создаем контакт
            contact_id = await get_or_create_chatwoot_contact(callback.from_user)
            
            # 2. Создаем диалог в Chatwoot
            if contact_id:
                conversation_id = await create_chatwoot_conversation(contact_id, user_id)
                
                # 3. Отправляем триггер "Оператор" в Chatwoot
                if conversation_id:
                    await send_message_to_chatwoot(user_id, "🔴 Пользователь запросил оператора")
            
            # 4. Сообщаем пользователю
            await callback.message.answer(
                "🔄 Соединяем с оператором...\n\n"
                "После завершения диалога напишите /menu для возврата к темам."
            )
            
            # Убираем клавиатуру
            await callback.message.edit_reply_markup(reply_markup=None)
            
        else:
            # Обычные темы
            answer_text = f"<b>{TOPICS[topic_index]}</b>\n\nОтвет на тему"
            await callback.message.edit_text(
                answer_text,
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
        # В режиме меню - показываем подсказку
        await message.answer(
            "Используйте меню выше или напишите /menu для выбора темы.\n"
            "Если нужен оператор, выберите 'Техническая поддержка' в меню."
        )
    else:
        # В режиме оператора - отправляем в Chatwoot
        success = await send_message_to_chatwoot(user_id, message.text)
        if not success:
            await message.answer("⚠️ Не удалось отправить сообщение оператору. Попробуйте еще раз.")

async def main():
    logging.info("Starting bot with Chatwoot integration...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
