# main.py — Fulfillment webhook для Dialogflow + Chatwoot handoff
# Деплой на Render / Vercel / Fly.io / любой сервис с HTTPS

import json
import logging
import os
from aiohttp import web
import aiohttp

# Настройки
CHATWOOT_URL = "https://help.redwallet.app"
CHATWOOT_API_TOKEN = "iAwyBVfycfViFrA8t5JZjd1R"          # ваш токен
CHATWOOT_ACCOUNT_ID = 1

logging.basicConfig(level=logging.INFO)

# Топики и ответы (Dialogflow будет их использовать, но здесь — fallback)
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
    """Чтобы стать мерчантом RedWallet, заполните форму для прохождения проверки на соответствие нашим требованиям.

Форма для подачи заявки: (ссылка)

На что мы обращаем внимание:
• Реальный ежемесячный оборот
• Репутация и отзывы

Срок рассмотрения: 3 рабочих дня""",

    # ... остальные 7 ответов ...

    """🔴 Пользователь запросил подключение к оператору. Соединяем..."""
]

async def send_chatwoot_handoff(conv_id):
    """Передаёт диалог оператору (handoff)"""
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conv_id}"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    data = {"status": "open"}  # open = assigned to agent

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    logging.info(f"Handoff выполнен для conversation {conv_id}")
                    return True
                else:
                    logging.error(f"Handoff failed: {resp.status} {await resp.text()}")
                    return False
    except Exception as e:
        logging.error(f"Ошибка handoff: {e}")
        return False

async def handle_fulfillment(request):
    try:
        req = await request.json()
        query_result = req.get("queryResult", {})
        intent = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})
        conversation_id = parameters.get("chatwoot_conversation_id")  # передаётся из Dialogflow

        logging.info(f"Intent: {intent} | Params: {parameters}")

        if intent == "Техническая поддержка" or intent == "Handoff":
            if conversation_id:
                success = await send_chatwoot_handoff(conversation_id)
                if success:
                    fulfillment_text = ANSWERS[-1]
                else:
                    fulfillment_text = "Не удалось соединить с оператором. Попробуйте позже."
            else:
                fulfillment_text = "Не удалось определить диалог. Напишите /operator."

        elif intent in ["Start", "Menu", "Default Welcome Intent"]:
            fulfillment_text = "📋 Выберите интересующую тему или задайте свой вопрос:"
            # Здесь Dialogflow сам добавит inline-клавиатуру через custom payload

        else:
            # fallback — пусть Dialogflow сам отвечает
            fulfillment_text = query_result.get("fulfillmentText", "Я не понял. Выберите тему в меню.")

        return web.json_response({
            "fulfillmentText": fulfillment_text,
            "fulfillmentMessages": [
                {"text": {"text": [fulfillment_text]}}
            ]
        })

    except Exception as e:
        logging.error(f"Ошибка в fulfillment: {e}")
        return web.json_response({
            "fulfillmentText": "Произошла ошибка. Попробуйте позже."
        }, status=500)

# === WEB-СЕРВЕР ===
app = web.Application()
app.router.add_post('/', handle_fulfillment)           # Dialogflow webhook обычно POST на /

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logging.info(f"Starting Dialogflow Fulfillment server on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)
