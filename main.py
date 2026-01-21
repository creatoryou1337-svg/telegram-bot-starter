import asyncio
import logging
import json
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"

# === НАСТРОЙКИ DIALOGFLOW ===
# Используем ваш Service Account
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "redwallet-wrvu",
    "private_key_id": "27e9a411c51ee42738dd947e36a53c56f33609fa",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDn6+6FXRNMu5Zz
mwPeTSu2qCdeSyYTU+pLEtmPLrnwzGk0l1WjpcL7U1B3aXVTdHVb8taFGHnjov09
4TQuDylNu+GYwylKP0O9FzdmRsVEGQEQvg29mkB977P/ZH/R6JlesDBEVW2/p2Bn
A5itl6mOTfbn0bLFuqDDH+Uz+GEdqU5VjSVhMEhDgyyzp8QQzMiwyX+zdZfqmAIi
k/ddFSJylQA8uqewwMz6xrO4uOcznl3x7dqFASeUzfCWgwDw6MbsGG58EWGcr0BL
XVUvTIFQGTFn5AHsslDEZmC8Jv6ADGCoSpq5ABlXPrfSIjAsLNyo5JOGRzC5o7wL
1al8RsbHAgMBAAECggEAJpZpSGmXk/f5jOuZBaxGXoJKO+n6AFOWfdOO55Veh6j4
b4Z8em7Slc7OFR2H/BDk6UhqwUNfcxdugOoPAgOGG50Wkzxpis/NkqZ3EmkqWkMP
cScwvGrFWeQqSTnXUJLIWJUCZY7nOfD8h7dKoxttsTPZ+xviCFHIfMlk8TQy3bm5
gpEYGvy7hFfFo99PtnCaw+j2Stw7uAuR4E1fBLeR4dx3Y47uGIqn9XPwKEgdBnWQ
a8sUdkiGcR/FBKTLf+aAxL5DVoNGhNj/Gy0REktUmBfV7ZnV/EI6mCLphixWoWXd
ZSfWnLD97rI7D2uy67uaboRq25vLfjGefFYWtZ81QQKBgQD1LfaqRhuxsvVe92PU
1IJQke3oQIqoD5WI9KQH1gpRN6Ok8yAgoFjmk2ARJ2smECfM4AQH01SWb9RlkRTt
R29331iD+F4wXNrRtIoJWlzTcmnxcJCmNT/9JZTwEQlbzGPFI4Dm+WAca+ILNzW+
sU3kZLJKkgmyVHa8V11QlUKBQQKBgQDyKC4c0bW/atC02JuDsyga/WO3QcZ5kg0b
QvuTpq0A9Qz1wW6SFFoZat3BjmvhW/+LLjcWqfdNMp4wjrm6mq/hstvAGKcY0H8Q
2iVy971bt4YgAdlWSobQYrlYQgTkJp57XrnMPxGfcrRhGEY9Xa8rjbYQ18E554va
wbelEse+BwKBgCT1S8R5Ev2jY1dwZU0Ux5wLk1g6OmyBBOKDNiK0QhPiFjnsKECi
yyPevVF4pq8zKjy43AKt+Yc/zj2NNCFcblIcicRC8TfLF3UbCN/GDk4VZiDt/fAA
AOhQ/PV/K/D5i2SRKIIovzMplAZqySA4q+wsva99+hY2ozta1AcsqLzBAoGAborT
CgrdWcVMAtJCo6s8Kp3zUCuxi7uVShWYvH1AyogS43jqnbq2qpWzJ3F5Y8XYcNOn
CCyMnOv3dJkixcFperFoSVe3p8c9yhabM9FN2rl7e878RLz+r8/xZg21J+VNQWor
jMZZqBz3pL8tCURj+5DURPoI1gMSP8lgqPVawy8CgYA71usYfT6Yjt4A/hQFFqzY
bGFEh6R/zgEV6glhsv4t2lc1ptprIKIDH4uNXg15qbCD4QG/e7GSzJTSiw8AfZPz
N04KWVELD9PXTHxQ2qAowx3mhc8lCUqUsUyITwBswPDc6iWmhrwIjJjqpmh4qPOf
vgR6kmPfmMDdv1eJFkbqgg==
-----END PRIVATE KEY-----""",
    "client_email": "redwallet@redwallet-wrvu.iam.gserviceaccount.com",
    "client_id": "104583849772551193257",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/redwallet%40redwallet-wrvu.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Dialogflow REST API (проще чем библиотека)
DIALOGFLOW_PROJECT_ID = "redwallet-wrvu"
DIALOGFLOW_SESSION_ID = "telegram-session"

# Или используем Dialogflow CX (проверьте в консоли Google)
# DIALOGFLOW_LOCATION = "global"
# DIALOGFLOW_AGENT_ID = "ваш-agent-id"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ОТПРАВКА В DIALOGFLOW ===
async def send_to_dialogflow(session_id: str, message: str):
    """Отправляем сообщение в Dialogflow через REST API"""
    
    # Получаем access token из service account
    import google.auth
    from google.oauth2 import service_account
    
    credentials = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    
    # Создаем авторизованную сессию
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token
    
    # URL для Dialogflow API
    url = f"https://dialogflow.googleapis.com/v2/projects/{DIALOGFLOW_PROJECT_ID}/agent/sessions/{session_id}:detectIntent"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "queryInput": {
            "text": {
                "text": message,
                "languageCode": "ru"
            }
        },
        "queryParams": {
            "timeZone": "Europe/Moscow"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Проверяем ответ Dialogflow
                    fulfillment_text = result.get("queryResult", {}).get("fulfillmentText", "")
                    intent = result.get("queryResult", {}).get("intent", {}).get("displayName", "")
                    
                    logging.info(f"Dialogflow response: intent={intent}, text={fulfillment_text[:50]}...")
                    
                    # Если Dialogflow вернул ответ, показываем его
                    if fulfillment_text:
                        return fulfillment_text
                    
                    # Если интент для оператора, Dialogflow сам передаст в Chatwoot
                    if intent in ["operator", "support", "human_agent"]:
                        return "🔄 Запрос передан оператору. Ожидайте ответа."
                    
                    return None
                    
                else:
                    error_text = await response.text()
                    logging.error(f"Dialogflow API error: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        logging.error(f"Dialogflow request error: {e}")
        return None

# === УПРОЩЕННАЯ ЛОГИКА БОТА ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в поддержку RedWallet!\n\n"
        "Задайте ваш вопрос или используйте команды:\n"
        "/menu - Показать меню тем\n"
        "/help - Помощь\n\n"
        "Напишите 'оператор' для связи с живым специалистом."
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    # Можно показать меню или отправить запрос в Dialogflow
    await message.answer(
        "📋 **Основные темы:**\n\n"
        "1. Как стать мерчантом\n"
        "2. Статус сделки\n"
        "3. Реферальная программа\n"
        "4. P2P-торговля\n"
        "5. Комиссии и лимиты\n"
        "6. Отзывы\n"
        "7. KYC и безопасность\n"
        "8. Сотрудничество\n"
        "9. Техническая поддержка\n\n"
        "Напишите номер темы или ваш вопрос."
    )

@dp.message(Command("operator"))
async def cmd_operator(message: types.Message):
    """Прямой вызов оператора"""
    user_id = message.from_user.id
    session_id = f"telegram-{user_id}"
    
    # Отправляем запрос оператора в Dialogflow
    response = await send_to_dialogflow(session_id, "оператор")
    
    if response:
        await message.answer(response)
    else:
        await message.answer("🔄 Соединяем с оператором...")

@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    
    if not text.strip():
        return
    
    # Создаем уникальную сессию для пользователя
    session_id = f"telegram-{user_id}"
    
    # Отправляем в Dialogflow
    dialogflow_response = await send_to_dialogflow(session_id, text)
    
    if dialogflow_response:
        # Если Dialogflow вернул ответ, показываем его
        await message.answer(dialogflow_response)
    else:
        # Если нет ответа, сообщаем что запрос обработан
        await message.answer("✅ Ваш запрос получен. Ожидайте ответа.")

async def main():
    logging.info("Starting bot with Dialogflow integration...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
