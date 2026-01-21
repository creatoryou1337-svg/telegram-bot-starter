import asyncio
import logging
import aiohttp
import json
from aiohttp import web

# === НАСТРОЙКИ ===
BOT_TOKEN = "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY"  # Нужен для проверки, но не используется напрямую
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
    """Чтобы стать мерчантом RedWallet, заполните форму для прохождения проверки на соответствие нашим требованиям.

Форма для подачи заявки:

На что мы обращаем внимание:
• Реальный ежемесячный оборот на нашей или других P2P-платформах
• Репутация и отзывы

Срок рассмотрения заявки:
• Ответ в течение 3 рабочих дней
• В отдельных случаях можем запросить дополнительные данные

После проверки вы получите сообщение с решением в @rwapp_bot. В случае одобрения мы отправим инструкции по дальнейшим действиям.""",

    """Информацию о статусе сделки вы можете посмотреть в приложении @rwapp_bot.

Если у вас возникла спорная ситуация или вопрос по сделке, подготовьте следующие данные:

• ID сделки или скриншот сделки
• Краткое описание ситуации

Наш специалист поддержки свяжется с вами прямо здесь после рассмотрения обращения.""",

    """Реферальная программа RedWallet позволяет получать процент с комиссии сделок приглашённых пользователей.

Ваша личная реферальная ссылка доступна в разделе Бонусы → Реферальная программа в приложении @rwapp_bot.

Дополнительная информация о программе также доступна в приложении.""",

    """P2P-торговля позволяет покупать и продавать криптовалюту напрямую между пользователями с защитой эскроу.

Express-покупки это быстрый способ купить криптовалюту по готовому предложению без создания ордера.

Все операции доступны в приложении @rwapp_bot.""",

    """Лимиты:
• Пополнение и вывод от 5 USD
• Минимальный ордер от 100 рублей

Комиссии:
Актуальные комиссии зависят от типа операции и сети и отображаются в приложении @rwapp_bot.

Для новых пользователей действует акция 0% комиссии. Подробности доступны в документации[](https://docs.redwallet.app/hc/faq/articles/1764657267-) и в приложении.""",

    """Отзывы пользователей о работе сервиса и P2P-сделках вы можете посмотреть в нашем канале: @redwallet_reviews""",

    """В RedWallet используется усиленная система верификации, необходимая для защиты пользователей и безопасной работы P2P-платформы. 
Она снижает риски мошенничества, исключает дропов и серые схемы и повышает надёжность сделок между пользователями.

В разделе Безопасность вы можете пройти верификацию и необходимые подтверждения, процесс занимает несколько минут и обычно проходит автоматически. 
Все данные обрабатываются в защищённом виде и используются только в рамках безопасности и разрешения спорных ситуаций.

Подробности и статус доступны в @rwapp_bot.""",

    """Вы можете оставить предложение о сотрудничестве прямо здесь в чате. Просто опишите вашу идею, формат или предложение в сообщении.

📧 Также вы можете написать нам на почту info@redwallet.app""",

    """🔴 Пользователь запросил подключение к оператору. Соединяем..."""
]

# === CHATWOOT API ФУНКЦИИ ===
async def send_chatwoot_message(conversation_id, content, message_type="outgoing"):
    """
    Отправляет сообщение в Chatwoot через API
    """
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN, 
        "Content-Type": "application/json"
    }
    data = {
        "content": content, 
        "message_type": message_type
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    logging.info(f"Message sent to conversation {conversation_id}: {content[:50]}...")
                    return True
                else:
                    error_text = await resp.text()
                    logging.error(f"Failed to send message: {resp.status} - {error_text}")
                    return False
    except Exception as e:
        logging.error(f"Exception sending message: {e}")
        return False

async def update_conversation_status(conversation_id, status="open"):
    """
    Обновляет статус разговора в Chatwoot (handoff к оператору)
    """
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}"
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN, 
        "Content-Type": "application/json"
    }
    data = {"status": status}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    logging.info(f"Conversation {conversation_id} status updated to {status}")
                    return True
                else:
                    error_text = await resp.text()
                    logging.error(f"Failed to update status: {resp.status} - {error_text}")
                    return False
    except Exception as e:
        logging.error(f"Exception updating status: {e}")
        return False

# === ЛОГИКА БОТА ===
async def process_message(data):
    """
    Обрабатывает webhook событие от Chatwoot
    """
    event = data.get('event')
    if event != 'message_created':
        logging.info(f"Ignoring event: {event}")
        return
    
    message = data.get('message', {})
    if message.get('message_type') != 'incoming':
        logging.info("Ignoring non-incoming message")
        return
    
    conversation = data.get('conversation', {})
    conv_id = conversation.get('id')
    inbox_id = conversation.get('inbox_id')
    
    # Получаем user_id из custom_attributes контакта
    sender = message.get('sender', {})
    contact = sender.get('contact', {})
    custom_attributes = contact.get('custom_attributes', {})
    user_id = custom_attributes.get('telegram_id')
    
    if not user_id:
        logging.warning("No telegram_id found in custom_attributes")
        return
    
    logging.info(f"Processing message from user {user_id} in conversation {conv_id}")
    
    # Инициализация состояния
    if user_id not in states:
        states[user_id] = {
            'state': 'menu', 
            'conversation_id': conv_id, 
            'inbox_id': inbox_id
        }
        logging.info(f"Initialized state for user {user_id}")
    
    user_state = states[user_id]
    content = message.get('content', '').strip()
    conv_id = user_state['conversation_id']
    
    state = user_state['state']
    
    if state == 'menu':
        if content.lower() in ['/start', '/menu']:
            # Показываем главное меню
            menu_text = "📋 Выберите интересующую тему или задайте свой вопрос:"
            await send_chatwoot_message(conv_id, menu_text)
            
        elif content.startswith('topic_'):
            try:
                topic_index = int(content.split('_')[1])
                if topic_index == 8:  # Техническая поддержка
                    user_state['state'] = 'operator'
                    # Handoff: меняем статус на open для оператора
                    await update_conversation_status(conv_id, "open")
                    await send_chatwoot_message(conv_id, ANSWERS[8])
                    
                else:
                    # Обычная тема
                    answer_text = f"<b>{TOPICS[topic_index]}</b>\n\n{ANSWERS[topic_index]}"
                    await send_chatwoot_message(conv_id, answer_text)
                    
            except (ValueError, IndexError):
                await send_chatwoot_message(conv_id, "Неизвестная команда. Используйте /menu для показа меню.")
                
        elif content == 'back_to_topics':
            menu_text = "📋 Выберите интересующую тему или задайте свой вопрос:"
            await send_chatwoot_message(conv_id, menu_text)
            
        else:
            # Неизвестное сообщение в режиме меню
            response = """Используйте меню выше или напишите /menu для выбора темы.
Если нужен оператор, выберите 'Техническая поддержка' в меню."""
            await send_chatwoot_message(conv_id, response)
            
    elif state == 'operator':
        # В режиме оператора - не вмешиваемся, сообщения идут напрямую оператору
        logging.info(f"User {user_id} in operator mode - passing message to human agent")
        pass
    
    else:
        logging.warning(f"Unknown state for user {user_id}: {state}")

# === WEBHOOK СЕРВЕР ===
async def webhook_handler(request):
    """
    Главный обработчик webhook от Chatwoot
    """
    try:
        data = await request.json()
        logging.info(f"Received webhook data: {json.dumps(data, indent=2)[:200]}...")
        await process_message(data)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logging.error(f"Error in webhook handler: {e}")
        return web.Response(text="ERROR", status=500)

# Создаём приложение aiohttp
app = web.Application()
app.router.add_post('/chatwoot-webhook', webhook_handler)

# === HEALTH CHECK ===
async def health_check(request):
    return web.Response(text="Bot is running", status=200)

app.router.add_get('/', health_check)

if __name__ == "__main__":
    logging.info("Starting RedWallet Bot Webhook Server...")
    logging.info(f"Webhook endpoint: /chatwoot-webhook")
    logging.info(f"Health check: /")
    web.run_app(app, host='0.0.0.0', port=8000)
