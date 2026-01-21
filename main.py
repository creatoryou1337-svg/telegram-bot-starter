import asyncio
import logging
import aiohttp
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

# === ВАШИ НАСТРОЙКИ CHATWOOT ===
CHATWOOT_API_URL = "https://help.redwallet.app"
CHATWOOT_API_TOKEN = "iAwyBVfycfViFrA8t5JZjd1R"
CHATWOOT_ACCOUNT_ID = "1"
CHATWOOT_INBOX_ID = "6"  # SuppRWapp_bot инбокс

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ХРАНИЛИЩА ===
user_states = {}  # True = меню, False = оператор
user_conversations = {}  # {user_id: conversation_id}
contact_cache = {}  # {user_id: contact_id}

# === CHATWOOT API ===
async def get_or_create_contact(user: types.User):
    """Получаем или создаем контакт в Chatwoot"""
    user_id = user.id
    
    if user_id in contact_cache:
        return contact_cache[user_id]
    
    # Ищем существующий контакт
    url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/search"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    search_data = {
        "q": str(user_id),
        "sort": "updated_at"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Поиск контакта
            async with session.post(url, headers=headers, json=search_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("payload") and len(data["payload"]) > 0:
                        contact_id = data["payload"][0]["id"]
                        contact_cache[user_id] = contact_id
                        return contact_id
            
            # Создаем новый контакт
            create_url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts"
            contact_data = {
                "inbox_id": CHATWOOT_INBOX_ID,
                "name": user.full_name or f"User{user.id}",
                "custom_attributes": {
                    "telegram_id": str(user.id),
                    "username": user.username or "no_username"
                }
            }
            
            async with session.post(create_url, headers=headers, json=contact_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    contact_id = data["payload"]["contact"]["id"]
                    contact_cache[user_id] = contact_id
                    return contact_id
                    
    except Exception as e:
        logging.error(f"Chatwoot contact error: {e}")
    
    return None

async def create_conversation(contact_id, user_id):
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
                    return conversation_id
    except Exception as e:
        logging.error(f"Create conversation error: {e}")
    
    return None

async def send_to_chatwoot(user_id, message_text):
    """Отправляем сообщение в Chatwoot"""
    if user_id not in user_conversations:
        return
    
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
                if resp.status != 200:
                    logging.error(f"Send to Chatwoot failed: {resp.status}")
    except Exception as e:
        logging.error(f"Send to Chatwoot error: {e}")

# === КОД БОТА (сокращенно) ===
# ... (ваша логика с меню и кнопками остается такой же)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = True
    
    # Создаем контакт и диалог в Chatwoot
    contact_id = await get_or_create_contact(message.from_user)
    if contact_id:
        await create_conversation(contact_id, user_id)
    
    await message.answer(
        "📋 Выберите интересующую тему или задайте свой вопрос:",
        reply_markup=get_main_keyboard()  # Ваша функция
    )

# ... остальной код бота

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
