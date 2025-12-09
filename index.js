// index.js - ФИНАЛЬНЫЙ ОБЪЕДИНЕННЫЙ КОД
require('dotenv').config();
const express = require('express');
const { Telegraf, Markup } = require('telegraf');
const sqlite3 = require('sqlite3').verbose();
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

// Проверка токена
if (!process.env.BOT_TOKEN) {
    console.error('❌ ОШИБКА: BOT_TOKEN не найден');
    process.exit(1);
}

const bot = new Telegraf(process.env.BOT_TOKEN);

// Middleware
app.use(express.json());
// Проверяем существование папки public
const fs = require('fs');
const path = require('path');

const publicPath = path.join(__dirname, 'public');
if (fs.existsSync(publicPath)) {
    app.use(express.static('public'));
} else {
    console.log('⚠️ Папка public не найдена, создаем временную страницу');
    
    // Создаем временный HTML
    app.get('/', (req, res) => {
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Telegram Clicker</title>
                <style>
                    body { font-family: Arial; padding: 50px; text-align: center; }
                    button { padding: 20px 40px; font-size: 24px; }
                </style>
            </head>
            <body>
                <h1>🎮 Telegram Clicker Mini App</h1>
                <p>Бот работает! Фронтенд скоро будет добавлен.</p>
                <button onclick="alert('+1 монета! 🪙')">👆 Кликни!</button>
            </body>
            </html>
        `);
    });
}

// База данных (SQLite)
const db = new sqlite3.Database('./game.db');

// Инициализация БД
db.serialize(() => {
    db.run(`
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            coins INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            multiplier REAL DEFAULT 1.0,
            per_click INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    `);
});

// Главная страница Mini App
app.get('/', (req, res) => {
    res.sendFile(__dirname + '/public/index.html');
});

// API endpoints для Mini App
app.get('/api/user-data', async (req, res) => {
    const telegramId = req.query.userId || req.query.tgid;
    
    db.get(
        `SELECT * FROM users WHERE telegram_id = ?`,
        [telegramId],
        (err, user) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            
            if (user) {
                res.json({
                    coins: user.coins,
                    clicks: user.clicks,
                    level: user.level,
                    multiplier: user.multiplier,
                    perClick: user.per_click
                });
            } else {
                // Создаем нового пользователя
                const userId = crypto.randomUUID();
                db.run(
                    `INSERT INTO users (id, telegram_id, coins, clicks, level, multiplier, per_click) 
                     VALUES (?, ?, 0, 0, 1, 1.0, 1)`,
                    [userId, telegramId],
                    function(err) {
                        if (err) {
                            res.status(500).json({ error: err.message });
                            return;
                        }
                        res.json({
                            coins: 0,
                            clicks: 0,
                            level: 1,
                            multiplier: 1.0,
                            perClick: 1
                        });
                    }
                );
            }
        }
    );
});

app.post('/api/save-data', (req, res) => {
    const { coins, clicks, level, multiplier, perClick, userId } = req.body;
    
    db.run(
        `UPDATE users SET 
            coins = ?, 
            clicks = ?, 
            level = ?, 
            multiplier = ?, 
            per_click = ?
         WHERE telegram_id = ?`,
        [coins, clicks, level, multiplier, perClick, userId],
        (err) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            res.json({ success: true });
        }
    );
});

// ============ ТЕЛЕГРАМ БОТ КЛИКЕР ============
// (код из вашего newbotjsrw.js)

// Хранение данных (временно в памяти, потом заменим на БД)
const userData = new Map();

// Функция для получения/создания пользователя
function getUser(userId) {
    if (!userData.has(userId)) {
        userData.set(userId, {
            coins: 0,
            clicks: 0,
            level: 1,
            multiplier: 1,
            lastClick: 0
        });
    }
    return userData.get(userId);
}

// Функция расчета награды
function calculateReward(user) {
    const base = 1;
    const levelBonus = Math.floor(user.level * 0.5);
    const randomBonus = Math.floor(Math.random() * 3);
    const total = (base + levelBonus + randomBonus) * user.multiplier;
    return Math.max(1, total);
}

// Функция проверки уровня
function checkLevelUp(user) {
    const oldLevel = user.level;
    user.level = Math.floor(user.clicks / 15) + 1;
    
    if (user.level > oldLevel) {
        return `🎉 **ПОВЫШЕНИЕ УРОВНЯ!** 🎉\nНовый уровень: ${user.level}`;
    }
    return null;
}

// Главное меню
function getMainMenu(userId) {
    const user = getUser(userId);
    
    const text = 
        `🎮 **КЛИКЕР GAME**\n\n` +
        `💰 Монеты: ${user.coins}\n` +
        `🏆 Уровень: ${user.level}\n` +
        `👆 Кликов: ${user.clicks}\n` +
        `⚡ Множитель: x${user.multiplier}\n\n` +
        `_Кликай кнопку ниже, чтобы заработать!_`;
    
    const keyboard = Markup.inlineKeyboard([
        [Markup.button.callback('👆 КЛИКНУТЬ!', 'click')],
        [
            Markup.button.callback('📊 Профиль', 'profile'),
            Markup.button.callback('🛒 Магазин', 'shop')
        ],
        [
            Markup.button.callback('🏆 Топ игроков', 'top'),
            Markup.button.callback('❓ Помощь', 'help')
        ]
    ]);
    
    return { text, keyboard };
}

// Команда /start
bot.start(async (ctx) => {
    const user = getUser(ctx.from.id);
    const menu = getMainMenu(ctx.from.id);
    
    await ctx.replyWithMarkdownV2(
        `🎮 Добро пожаловать в *Clicker Game*, ${ctx.from.first_name}\\!\n` +
        `Ты начинаешь с ${user.coins} монет\\.\n` +
        `*Кликай кнопку ниже и начинай зарабатывать\\!*`,
        menu.keyboard
    );
});

// Обработка кликов
bot.action('click', async (ctx) => {
    const userId = ctx.from.id;
    const user = getUser(userId);
    
    // Проверка на спам (максимум 5 кликов в секунду)
    const now = Date.now();
    if (now - user.lastClick < 200) {
        await ctx.answerCbQuery('⚠️ Не так быстро!');
        return;
    }
    
    user.lastClick = now;
    
    // Начисляем награду
    const reward = calculateReward(user);
    user.coins += reward;
    user.clicks += 1;
    
    // Проверяем повышение уровня
    const levelUpMessage = checkLevelUp(user);
    
    // Ответ пользователю
    await ctx.answerCbQuery(`+${reward} монет! 🪙`);
    
    // Обновляем сообщение
    const menu = getMainMenu(userId);
    
    let message = menu.text;
    if (levelUpMessage) {
        message = levelUpMessage + '\n\n' + message;
    }
    
    try {
        await ctx.editMessageText(message, {
            parse_mode: 'Markdown',
            ...menu.keyboard
        });
    } catch (error) {
        // Если сообщение старое, отправляем новое
        await ctx.replyWithMarkdown(message, menu.keyboard);
    }
});

// Профиль
bot.action('profile', async (ctx) => {
    const user = getUser(ctx.from.id);
    
    const progress = (user.clicks % 15) / 15 * 100;
    const progressBar = '█'.repeat(Math.floor(progress / 10)) + 
                       '░'.repeat(10 - Math.floor(progress / 10));
    
    await ctx.editMessageText(
        `👤 *ВАШ ПРОФИЛЬ*\n\n` +
        `💰 Монеты: *${user.coins}*\n` +
        `🏆 Уровень: *${user.level}*\n` +
        `👆 Всего кликов: *${user.clicks}*\n` +
        `⚡ Множитель: *x${user.multiplier}*\n\n` +
        `📊 Прогресс до след. уровня:\n` +
        `${progressBar} ${Math.floor(progress)}%\n` +
        `Осталось кликов: *${15 - (user.clicks % 15)}*\n\n` +
        `_Кликай больше для повышения уровня!_`,
        {
            parse_mode: 'Markdown',
            ...Markup.inlineKeyboard([
                [Markup.button.callback('🔙 На главную', 'back')]
            ])
        }
    );
});

// Магазин улучшений
bot.action('shop', async (ctx) => {
    const user = getUser(ctx.from.id);
    
    const upgrades = [
        {
            id: 'multiplier_2',
            name: '⚡ Множитель x2',
            price: 50,
            description: 'Удваивает награду за каждый клик',
            effect: (user) => user.multiplier *= 2
        },
        {
            id: 'multiplier_3',
            name: '🔥 Множитель x3',
            price: 150,
            description: 'Утраивает награду за каждый клик',
            effect: (user) => user.multiplier *= 3
        },
        {
            id: 'bonus_10',
            name: '🎁 Бонус +10 монет',
            price: 30,
            description: 'Мгновенно добавляет 10 монет',
            effect: (user) => user.coins += 10
        },
        {
            id: 'level_up',
            name: '🚀 Повышение уровня',
            price: 200,
            description: 'Мгновенно повышает уровень на 1',
            effect: (user) => user.level += 1
        }
    ];
    
    const buttons = upgrades.map(upgrade => [
        Markup.button.callback(
            `${upgrade.name} - ${upgrade.price} монет`,
            `buy_${upgrade.id}`
        )
    ]);
    
    buttons.push([Markup.button.callback('🔙 На главную', 'back')]);
    
    await ctx.editMessageText(
        `🛒 *МАГАЗИН УЛУЧШЕНИЙ*\n\n` +
        `💰 Ваш баланс: *${user.coins}* монет\n\n` +
        `*Доступные улучшения:*\n` +
        upgrades.map(u => 
            `• ${u.name} - ${u.price} монет\n  ${u.description}`
        ).join('\n\n'),
        {
            parse_mode: 'Markdown',
            ...Markup.inlineKeyboard(buttons)
        }
    );
});

// Покупка улучшений
bot.action(/buy_(.+)/, async (ctx) => {
    const upgradeId = ctx.match[1];
    const user = getUser(ctx.from.id);
    
    const upgrades = {
        'multiplier_2': { price: 50, effect: (u) => u.multiplier *= 2, name: 'Множитель x2' },
        'multiplier_3': { price: 150, effect: (u) => u.multiplier *= 3, name: 'Множитель x3' },
        'bonus_10': { price: 30, effect: (u) => u.coins += 10, name: 'Бонус +10 монет' },
        'level_up': { price: 200, effect: (u) => u.level += 1, name: 'Повышение уровня' }
    };
    
    const upgrade = upgrades[upgradeId];
    
    if (!upgrade) {
        await ctx.answerCbQuery('❌ Улучшение не найдено');
        return;
    }
    
    if (user.coins < upgrade.price) {
        await ctx.answerCbQuery(`❌ Недостаточно монет! Нужно: ${upgrade.price}`);
        return;
    }
    
    // Покупаем
    user.coins -= upgrade.price;
    upgrade.effect(user);
    
    await ctx.answerCbQuery(`✅ Куплено: ${upgrade.name}`);
    
    // Возвращаем в магазин
    const shopKeyboard = Markup.inlineKeyboard([
        [Markup.button.callback('🛒 Вернуться в магазин', 'shop')],
        [Markup.button.callback('🔙 На главную', 'back')]
    ]);
    
    await ctx.editMessageText(
        `✅ *УСПЕШНАЯ ПОКУПКА!*\n\n` +
        `Вы купили: *${upgrade.name}*\n` +
        `💰 Потрачено: *${upgrade.price}* монет\n` +
        `💰 Осталось: *${user.coins}* монет\n\n` +
        `_Приятной игры!_`,
        {
            parse_mode: 'Markdown',
            ...shopKeyboard
        }
    );
});

// Топ игроков
bot.action('top', async (ctx) => {
    const topUsers = Array.from(userData.entries())
        .map(([id, data]) => ({ id, ...data }))
        .sort((a, b) => b.coins - a.coins)
        .slice(0, 10);
    
    let topText = `🏆 *ТОП 10 ИГРОКОВ*\n\n`;
    
    if (topUsers.length === 0) {
        topText += `Пока никого нет. Будь первым!`;
    } else {
        topUsers.forEach((user, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            topText += `${medal} Игрок ${user.id}: *${user.coins}* монет (Ур. ${user.level})\n`;
        });
    }
    
    await ctx.editMessageText(
        topText,
        {
            parse_mode: 'Markdown',
            ...Markup.inlineKeyboard([
                [Markup.button.callback('🔙 На главную', 'back')]
            ])
        }
    );
});

// Помощь
bot.action('help', async (ctx) => {
    await ctx.editMessageText(
        `❓ *ПОМОЩЬ И ПРАВИЛА*\n\n` +
        `*Как играть:*\n` +
        `1. Нажимай кнопку "👆 КЛИКНУТЬ!"\n` +
        `2. Зарабатывай монеты\n` +
        `3. Повышай уровень (каждые 15 кликов)\n` +
        `4. Покупай улучшения в магазине\n\n` +
        `*Особенности:*\n` +
        `• Каждый уровень увеличивает награду\n` +
        `• Улучшения умножают доход\n` +
        `• Нет ограничений по времени\n\n` +
        `*Команды:*\n` +
        `/start - начать игру\n` +
        `/menu - открыть меню\n` +
        `/stats - ваша статистика\n\n` +
        `_Удачи в игре!_ 🍀`,
        {
            parse_mode: 'Markdown',
            ...Markup.inlineKeyboard([
                [Markup.button.callback('🔙 На главную', 'back')]
            ])
        }
    );
});

// Возврат на главную
bot.action('back', async (ctx) => {
    const menu = getMainMenu(ctx.from.id);
    await ctx.editMessageText(menu.text, {
        parse_mode: 'Markdown',
        ...menu.keyboard
    });
});

// Команда /menu
bot.command('menu', async (ctx) => {
    const menu = getMainMenu(ctx.from.id);
    await ctx.replyWithMarkdown(menu.text, menu.keyboard);
});

// Команда /stats
bot.command('stats', async (ctx) => {
    const user = getUser(ctx.from.id);
    await ctx.replyWithMarkdown(
        `📊 *ВАША СТАТИСТИКА*\n\n` +
        `💰 Монеты: *${user.coins}*\n` +
        `🏆 Уровень: *${user.level}*\n` +
        `👆 Всего кликов: *${user.clicks}*\n` +
        `⚡ Множитель: *x${user.multiplier}*\n\n` +
        `_Продолжай в том же духе!_`
    );
});

// Команда /bonus (секретная команда)
bot.command('bonus', async (ctx) => {
    const user = getUser(ctx.from.id);
    const bonus = 100;
    user.coins += bonus;
    
    await ctx.replyWithMarkdown(
        `🎁 *СЕКРЕТНЫЙ БОНУС!*\n\n` +
        `Вы получили: *+${bonus}* монет!\n` +
        `💰 Теперь у вас: *${user.coins}* монет\n\n` +
        `_Удачи в игре!_ 🍀`
    );
});

// Обработка ошибок
bot.catch((err, ctx) => {
    console.error('❌ Ошибка бота:', err);
    if (ctx.updateType === 'callback_query') {
        ctx.answerCbQuery('⚠️ Произошла ошибка. Попробуйте снова.');
    }
});

// ============ ЗАПУСК СЕРВЕРА ============
app.listen(PORT, () => {
    console.log(`🚀 Сервер запущен на порту ${PORT}`);
    
    // Установка вебхука для бота
    if (process.env.RENDER_EXTERNAL_URL) {
        const webhookUrl = `${process.env.RENDER_EXTERNAL_URL}/webhook`;
        bot.telegram.setWebhook(webhookUrl);
        console.log('✅ Webhook установлен:', webhookUrl);
        
        // Запуск бота в вебхук режиме
        console.log('🤖 Бот запущен в режиме вебхука');
    } else {
        // Для локальной разработки
        bot.launch()
            .then(() => {
                console.log('🤖 Бот запущен в режиме разработки (polling)');
                console.log('================================');
                console.log('✅ КЛИКЕР УСПЕШНО ЗАПУЩЕН!');
                console.log('================================');
            })
            .catch(err => {
                console.error('❌ Ошибка запуска бота:', err);
            });
    }
    
    console.log('🌐 Mini App доступен по адресу: /');
    console.log('📱 API endpoints: /api/user-data, /api/save-data');
});

// Элегантное завершение
process.once('SIGINT', () => {
    console.log('\n🛑 Остановка бота...');
    bot.stop('SIGINT');
    process.exit(0);
});

process.once('SIGTERM', () => {
    console.log('\n🛑 Завершение работы...');
    bot.stop('SIGTERM');
    process.exit(0);
});
