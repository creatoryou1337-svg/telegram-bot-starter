import asyncio
import logging
import os
import json

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import requests

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "7638473239:AAE87V8T6Xdn0kCQg9rg1KPW1MuociDwWaY")
WEBHOOK_TELEGRAM_PATH = "/webhook/telegram"
WEBHOOK_CHATWOOT_PATH = "/webhook/chatwoot"
WEBHOOK_TELEGRAM_URL = f"https://supprwapp-bot.onrender.com{WEBHOOK_TELEGRAM_PATH}"
WEBHOOK_CHATWOOT_URL = f"https://supprwapp-bot.onrender.com{WEBHOOK_CHATWOOT_PATH}"

# Chatwoot настройки
CHATWOOT_API_TOKEN = "iAwyBVfycfVIFrA8t5JZjd1R"
CHATWOOT_BASE_URL = "https://help.redwallet.app"
CHATWOOT_ACCOUNT_ID = 1
CHATWOOT_INBOX_ID = 1

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ДАННЫЕ МЕНЮ ==========
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
    # 1
    "Чтобы стать мерчантом RedWallet, заполните форму для прохождения проверки на соответствие нашим требованиям.\n\n"
    "Форма для подачи заявки:\n\n"
    "На что мы обращаем внимание:\n• Реальный ежемесячный оборот на нашей или других P2P-платформах\n• Репутация и отзывы\n\n"
    "Срок рассмотрения заявки:\n• Ответ в течение 3 рабочих дней\n• В отдельных случаях можем запросить дополнительные данные\n\n"
    "После проверки вы получите сообщение с решением в @rwapp_bot. В случае одобрения мы отправим инструкции по дальнейшим действиям.",
    
    # 2
    "Информацию о статусе сделки вы можете посмотреть в приложении @rwapp_bot.\n\n"
    "Если у вас возникла спорная ситуация или вопрос по сделке, подготовьте следующие данные:\n\n"
    "• ID сделки или скриншот сделки\n• Краткое описание ситуации\n\n"
    "Наш специалист поддержки свяжется с вами прямо здесь после рассмотрения обращения.",
    
    # 3
    "Реферальная программа RedWallet позволяет получать процент с комиссии сделок приглашённых пользователей.\n\n"
    "Ваша личная реферальная ссылка доступна в разделе Бонусы → Реферальная программа в приложении @rwapp_bot.\n\n"
    "Дополнительная информация о программе также доступна в приложении.",
    
    # 4
    "P2P-торговля позволяет покупать и продавать криптовалюту напрямую между пользователями с защитой эскроу.\n\n"
    "Express-покупки это быстрый способ купить криптовалюту по готовому предложению без создания ордера.\n\n"
    "Все операции доступны в приложении @rwapp_bot.",
    
    # 5
    "Лимиты:\n• Пополнение и вывод от 5 USD\n• Минимальный ордер от 100 рублей\n\n"
    "Комиссии:\nАктуальные комиссии зависят от типа операции и сети и отображаются в приложении @rwapp_bot.\n\n"
    "Для новых пользователей действует акция 0% комиссии. Подробности доступны в документации "
    "(https://docs.redwallet.app/hc/faq/articles/1764657267-) и в приложении.",
    
    # 6
    "Отзывы пользователей о работе сервиса и P2P-сделках вы можете посмотреть в нашем канале: @redwallet_reviews",
    
    # 7
    "В RedWallet используется усиленная система верификации, необходимая для защиты пользователей и безопасной работы P2P-платформы. "
    "Она снижает риски мошенничества, исключает дропов и серые схемы и повышает надёжность сделок между пользователей.\n\n"
    "В разделе Безопасность вы можете пройти верификацию и необходимые подтверждения, процесс занимает несколько минут и обычно проходит автоматически. "
    "Все данные обрабатываются в защищённом виде и используются только в рамках безопасности и разрешения спорных ситуаций.\n\n"
    "Подробности и статус доступны в @rwapp_bot.",
    
    # 8
    "Вы можете оставить предложение о сотрудничестве прямо здесь в чате. Просто опишите вашу идею, формат или предложение в сообщении.\n\n"
    "📧 Также вы можете написать нам на почту info@redwallet.app",
    
    # 9
    "Оператор"
]

# ========== СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ ==========
user_states = {}
user_chatwoot_conversations = {}

# ========== КЛАВИАТУРЫ ==========
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
    buttons = [[types.InlineKeyboardButton(text="↩ Назад к темам", callback_data="back_to_topics")]]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== CHATWOOT API ФУНКЦИИ ==========
async def get_or_create_chatwoot_contact(user_id, user_name="Telegram User"):
    """Создает или возвращает контакт в Chatwoot"""
    try:
        headers = {"api_access_token": CHATWOOT_API_TOKEN}
        
        # Создание контакта
        create_url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts"
        payload = {
            "inbox_id": CHATWOOT_INBOX_ID,
            "name": user_name,
            "source_id": f"telegram_{user_id}"
        }
        
        response = requests.post(create_url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["payload"]["contact"]["id"]
        else:
            print(f"Ошибка создания контакта: {response.status_code}, {response.text}")
            
    except Exception as e:
        print(f"Ошибка создания контакта Chatwoot: {e}")
    return None

async def send_to_chatwoot(user_id, message_text, user_name=None):
    """Отправляет сообщение пользователя в Chatwoot"""
    try:
        if not user_name:
            user_name = f"Telegram User {user_id}"
        
        contact_id = await get_or_create_chatwoot_contact(user_id, user_name)
        if not contact_id:
            print(f"Не удалось создать/найти контакт для user_id: {user_id}")
            return False
        
        headers = {"api_access_token": CHATWOOT_API_TOKEN}
        
        # Создание диалога
        conv_url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations"
        payload = {
            "inbox_id": CHATWOOT_INBOX_ID,
            "contact_id": contact_id,
            "source_id": f"telegram_{user_id}"
        }
        
        response = requests.post(conv_url, json=payload, headers=headers)
        if response.status_code == 200:
            conversation_id = response.json()["id"]
            user_chatwoot_conversations[user_id] = conversation_id
            
            # Отправка сообщения
            message_url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
            payload = {
                "content": message_text,
                "message_type": "incoming"
            }
            
            msg_response = requests.post(message_url, json=payload, headers=headers)
            if msg_response.status_code == 200:
                print(f"✅ Сообщение отправлено в Chatwoot (user: {user_id}): {message_text}")
                return True
            else:
                print(f"❌ Ошибка отправки сообщения: {msg_response.status_code}, {msg_response.text}")
        else:
            print(f"❌ Ошибка создания диалога: {response.status_code}, {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки в Chatwoot: {e}")
    return False

# ========== ОБРАБОТЧИКИ TELEGRAM ==========
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

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    # Проверка состояния
    if not user_states.get(user_id, True):
        await callback.answer("Закончите диалог с оператором, затем используйте /menu", show_alert=True)
        return
    
    if data.startswith("topic_"):
        try:
            topic_index = int(data.split("_")[1])
            
            if topic_index == 8:  # Техническая поддержка
                user_states[user_id] = False  # Блокируем меню
                
                # Отправляем в Chatwoot
                user_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
                if not user_name:
                    user_name = f"User {user_id}"
                    
                success = await send_to_chatwoot(user_id, "Пользователь запросил оператора", user_name)
                
                if success:
                    # Сообщения пользователю
                    await callback.message.answer("Оператор")
                    await callback.message.answer(
                        "🔄 Соединяем с оператором...\n\n"
                        "Теперь вы можете общаться с оператором напрямую.\n"
                        "После завершения диалога напишите /menu для возврата к темам."
                    )
                else:
                    await callback.message.answer("⚠️ Не удалось соединить с оператором. Попробуйте позже.")
                    user_states[user_id] = True  # Разблокируем меню
                
                await callback.message.edit_reply_markup(reply_markup=None)
                
            else:
                # Обычные темы
                await callback.message.edit_text(
                    f"<b>{TOPICS[topic_index]}</b>\n\n{ANSWERS[topic_index]}",
                    reply_markup=get_back_keyboard(),
                    parse_mode="HTML"
                )
                
        except (ValueError, IndexError) as e:
            await callback.answer("Ошибка: тема не найдена")
    
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
    
    # Игнорируем команды
    if message.text and message.text.startswith('/'):
        return
    
    # Если в режиме меню
    if user_states.get(user_id, True):
        await message.answer(
            "Используйте меню выше или напишите /menu для выбора темы.\n"
            "Если нужен оператор, выберите 'Техническая поддержка' в меню."
        )
    else:
        # В режиме оператора - отправляем в Chatwoot
        user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        if not user_name:
            user_name = f"User {user_id}"
            
        success = await send_to_chatwoot(user_id, message.text, user_name)
        if not success:
            await message.answer("⚠️ Не удалось отправить сообщение оператору. Попробуйте снова или напишите /menu")

# ========== ОБРАБОТЧИК CHATWOOT WEBHOOK ==========
async def chatwoot_webhook_handler(request):
    """Принимает вебхуки от Chatwoot"""
    try:
        data = await request.json()
        event = data.get("event")
        print(f"📨 Chatwoot webhook received: {event}")
        
        if event == "message_created":
            message = data.get("message", {})
            # Только сообщения ОТ оператора
            if message.get("message_type") == "outgoing":
                content = message.get("content")
                conversation = data.get("conversation", {})
                contact = conversation.get("contact", {})
                
                # Ищем user_id
                source_id = contact.get("source_id", "")
                if source_id.startswith("telegram_"):
                    user_id = int(source_id.replace("telegram_", ""))
                    
                    # Отправляем пользователю
                    await bot.send_message(user_id, content)
                    print(f"✅ Отправлено пользователю {user_id}: {content}")
        
        elif event == "conversation_status_changed":
            # Если диалог закрыт, разблокируем меню
            conversation = data.get("conversation", {})
            if conversation.get("status") in ["resolved", "closed"]:
                contact = conversation.get("contact", {})
                source_id = contact.get("source_id", "")
                if source_id.startswith("telegram_"):
                    user_id = int(source_id.replace("telegram_", ""))
                    user_states[user_id] = True  # Разблокируем меню
                    print(f"🔓 Диалог завершен, меню разблокировано для {user_id}")
        
        return web.Response(text="OK", status=200)
        
    except Exception as e:
        print(f"❌ Chatwoot webhook error: {e}")
        return web.Response(text="Error", status=500)

# ========== HEALTH CHECK ==========
async def health_check(request):
    return web.Response(text="✅ Bot is running")

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
async def main():
    print("=" * 50)
    print("🚀 Запуск бота RedWallet Support...")
    print("=" * 50)
    print(f"🤖 Telegram webhook URL: {WEBHOOK_TELEGRAM_URL}")
    print(f"🔄 Chatwoot webhook URL: {WEBHOOK_CHATWOOT_URL}")
    print(f"📊 Chatwoot API: {CHATWOOT_BASE_URL}")
    print("=" * 50)
    
    # Установка вебхука для Telegram
    try:
        await bot.set_webhook(WEBHOOK_TELEGRAM_URL)
        print("✅ Telegram webhook установлен")
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
    
    # Создание сервера
    app = web.Application()
    
    # 1. Вебхук для Telegram
    telegram_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    telegram_handler.register(app, path=WEBHOOK_TELEGRAM_PATH)
    
    # 2. Вебхук для Chatwoot
    app.router.add_post(WEBHOOK_CHATWOOT_PATH, chatwoot_webhook_handler)
    
    # 3. Health check endpoints
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_get("/test", lambda r: web.Response(text="Test OK"))
    
    setup_application(app, dp, bot=bot)
    
    # Запуск сервера
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    
    print(f"✅ Сервер запущен на порту {port}")
    print("✅ Бот готов к работе")
    print("=" * 50)
    print("📝 Используйте /start или /menu в Telegram")
    print("=" * 50)
    
    # Бесконечный цикл
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
