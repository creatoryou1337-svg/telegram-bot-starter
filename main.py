import asyncio
import logging
import aiohttp
import json
from aiohttp import web

# === НАСТРОЙКИ ===
BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"  # Не используется напрямую, но нужен для проверки
CHATWOOT_URL = "https://help.redwallet.app"
CHATWOOT_API_TOKEN = "iAwyBVfycfViFrA8t5JZjd1R"
ACCOUNT_ID = 1

# Логирование
logging.basicConfig(level=logging.INFO)

# === ХРАНИЛИЩА ===
states = {}  # user_id: {'state': 'menu' or 'operator', 'conversation_id': id, 'inbox_id': id}

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
    "Чтобы стать мерчантом RedWallet, заполните форму для прохождения проверки на соответствие нашим требованиям.\n\n"
    "Форма для подачи заявки:\n\n"
    "На что мы обращаем внимание:\n• Реальный ежемесячный оборот на нашей или других P2P-платформах\n• Репутация и отзывы\n\n"
    "Срок рассмотрения заявки:\n• Ответ в течение 3 рабочих дней\n• В отдельных случаях можем запросить дополнительные данные\n\n"
    "После проверки вы получите сообщение с решением в @rwapp_bot. В случае одобрения мы отправим инструкции по дальнейшим действиям.",
    
    "Информацию о статусе сделки вы можете посмотреть в приложении @rwapp_bot.\n\n"
    "Если у вас возникла спорная ситуация или вопрос по сделке, подготовьте следующие данные:\n\n"
    "• ID сделки или скриншот сделки\n• Краткое описание ситуации\n\n"
    "Наш специалист поддержки свяжется с вами прямо здесь после рассмотрения обращения.",
    
    "Реферальная программа RedWallet позволяет получать процент с комиссии сделок приглашённых пользователей.\n\n"
    "Ваша личная реферальная ссылка доступна в разделе Бонусы → Реферальная программа в приложении @rwapp_bot.\n\n"
    "Дополнительная информация о программе также доступна в приложении.",
    
    "P2P-торговля позволяет покупать и продавать криптовалюту напрямую между пользователями с защитой эскроу.\n\n"
    "Express-покупки это быстрый способ купить криптовалюту по готовому предложению без создания ордера.\n\n"
    "Все операции доступны в приложении @rwapp_bot.",
    
    "Лимиты:\n• Пополнение и вывод от 5 USD\n• Минимальный ордер от 100 рублей\n\n"
    "Комиссии:\nАктуальные комиссии зависят от типа операции и сети и отображаются в приложении @rwapp_bot.\n\n"
    "Для новых пользователей действует акция 0% комиссии. Подробности доступны в документации "
    [](https://docs.redwallet.app/hc/faq/articles/1764657267-) и в приложении.",
    
    "Отзывы пользователей о работе сервиса и P2P-сделках вы можете посмотреть в нашем канале: @redwallet_reviews",
    
    "В RedWallet используется усиленная система верификации, необходимая для защиты пользователей и безопасной работы P2P-платформы. "
    "Она снижает риски мошенничества, исключает дропов и серые схемы и повышает надёжность сделок между пользователей.\n\n"
    "В разделе Безопасность вы можете пройти верификацию и необходимые подтверждения, процесс занимает несколько минут и обычно проходит автоматически. "
    "Все данные обрабатываются в защищённом виде и используются только в рамках безопасности и разрешения спорных ситуаций.\n\n"
    "Подробности и статус доступны в @rwapp_bot.",
    
    "Вы можете оставить предложение о сотрудничестве прямо здесь в чате. Просто опишите вашу идею, формат или предложение в сообщении.\n\n"
    "📧 Также вы можете написать нам на почту info@redwallet.app",
    
    "🔴 Пользователь запросил подключение к оператору. Соединяем..."
]

# === CHATWOOT API ФУНКЦИИ ===
async def send_chatwoot_message(conversation_id, content, attachments=None):
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}/messages"
    headers = {"api_access_token": CHATWOOT_API_TOKEN, "Content-Type": "application/json"}
    data = {"content": content, "message_type": "outgoing"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status != 200:
                logging.error(f"Failed to send message: {await resp.text()}")
            else:
                logging.info("Message sent to user")

async def update_conversation_status(conversation_id, status="open"):
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}"
    headers = {"api_access_token": CHATWOOT_API_TOKEN, "Content-Type": "application/json"}
    data = {"status": status}
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=data) as resp:
            if resp.status != 200:
                logging.error(f"Failed to update status: {await resp.text()}")
            else:
                logging.info(f"Conversation status updated to {status}")

# === ЛОГИКА БОТА ===
async def process_message(data):
    event = data.get('event')
    if event != 'message_created':
        return
    
    message = data['message']
    if message['message_type'] != 'incoming':
        return
    
    conversation = data['conversation']
    conv_id = conversation['id']
    inbox_id = conversation['inbox_id']
    user_id = message['sender']['id']  # Telegram user ID from custom_attributes
    
    # Инициализация состояния
    if user_id not in states:
        states[user_id] = {'state': 'menu', 'conversation_id': conv_id, 'inbox_id': inbox_id}
    
    state = states[user_id]['state']
    content = message['content']
    
    if state == 'menu':
        if content.lower() == '/start' or content.lower() == '/menu':
            await send_chatwoot_message(conv_id, "📋 Выберите интересующую тему или задайте свой вопрос:", attachments=[get_main_keyboard()])
        elif content.startswith('topic_'):
            topic_index = int(content.split('_')[1])
            if topic_index == 8:  # Техподдержка
                states[user_id]['state'] = 'operator'
                await update_conversation_status(conv_id, "open")  # Handoff: меняем на open для оператора
                await send_chatwoot_message(conv_id, ANSWERS[8])
            else:
                await send_chatwoot_message(conv_id, f"<b>{TOPICS[topic_index]}</b>\n\n{ANSWERS[topic_index]}", attachments=[get_back_keyboard()])
        elif content == 'back_to_topics':
            await send_chatwoot_message(conv_id, "📋 Выберите интересующую тему или задайте свой вопрос:", attachments=[get_main_keyboard()])
        else:
            await send_chatwoot_message(conv_id, "Используйте меню или напишите /menu.")
    elif state == 'operator':
        # Сообщения идут оператору как есть, бот не вмешивается
        pass

# === КЛАВИАТУРЫ (как JSON для Chatwoot attachments) ===
def get_main_keyboard():
    buttons = []
    for i in range(0, len(TOPICS), 2):
        row = []
        row.append({"type": "postback", "title": TOPICS[i], "payload": f"topic_{i}"})
        if i + 1 < len(TOPICS):
            row.append({"type": "postback", "title": TOPICS[i+1], "payload": f"topic_{i+1}"})
        buttons.append(row)
    return {"type": "template", "template_type": "button", "text": "Меню", "buttons": buttons}  # Адаптировано под Chatwoot Telegram attachments

def get_back_keyboard():
    return {"type": "template", "template_type": "button", "text": "Назад", "buttons": [{"type": "postback", "title": "↩ Назад к темам", "payload": "back_to_topics"}]}

# === WEBHOOK СЕРВЕР ===
async def webhook_handler(request):
    data = await request.json()
    logging.info(f"Received webhook: {json.dumps(data, indent=2)}")
    await process_message(data)
    return web.Response(text="OK")

app = web.Application()
app.router.add_post('/chatwoot-webhook', webhook_handler)

if __name__ == "__main__":
    web.run_app(app, port=8000)  # Запустите на сервере, используйте ngrok для теста
