// index.js - ПОЛНЫЙ КОД TELEGRAM CLICKER
require('dotenv').config();
const express = require('express');
const { Telegraf, Markup } = require('telegraf');
const sqlite3 = require('sqlite3').verbose();
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// ============ НАСТРОЙКИ СЕРВЕРА ============
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Принудительный HTTPS для продакшена
app.use((req, res, next) => {
    if (req.headers['x-forwarded-proto'] !== 'https' && process.env.NODE_ENV === 'production') {
        return res.redirect('https://' + req.headers.host + req.url);
    }
    next();
});

// CORS headers
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// ============ ПРОВЕРКА ТОКЕНА ============
if (!process.env.BOT_TOKEN) {
    console.error('❌ ОШИБКА: BOT_TOKEN не найден в .env файле');
    process.exit(1);
}

const bot = new Telegraf(process.env.BOT_TOKEN);

// ============ БАЗА ДАННЫХ SQLite ============
const db = new sqlite3.Database('./game.db');

// Инициализация БД
db.serialize(() => {
    // Таблица пользователей
    db.run(`
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            coins INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            multiplier REAL DEFAULT 1.0,
            per_click INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            last_click TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    `);

    // Таблица улучшений пользователей
    db.run(`
        CREATE TABLE IF NOT EXISTS user_upgrades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            upgrade_type TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    `);

    // Таблица достижений
    db.run(`
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    `);

    console.log('✅ База данных инициализирована');
});

// ============ ФУНКЦИИ БАЗЫ ДАННЫХ ============

// Сохранение пользователя в БД
async function saveUserToDB(telegramId, userData) {
    return new Promise((resolve, reject) => {
        const now = new Date().toISOString();
        
        db.get(
            `SELECT * FROM users WHERE telegram_id = ?`,
            [telegramId],
            (err, user) => {
                if (err) {
                    reject(err);
                    return;
                }

                if (user) {
                    // Обновляем существующего пользователя
                    db.run(
                        `UPDATE users SET 
                            coins = ?,
                            clicks = ?,
                            level = ?,
                            multiplier = ?,
                            per_click = ?,
                            experience = ?,
                            updated_at = ?
                         WHERE telegram_id = ?`,
                        [
                            userData.coins,
                            userData.clicks,
                            userData.level,
                            userData.multiplier,
                            userData.perClick || 1,
                            userData.experience || 0,
                            now,
                            telegramId
                        ],
                        (err) => {
                            if (err) reject(err);
                            else resolve();
                        }
                    );
                } else {
                    // Создаем нового пользователя
                    const userId = crypto.randomUUID();
                    db.run(
                        `INSERT INTO users 
                         (id, telegram_id, username, first_name, last_name, 
                          coins, clicks, level, multiplier, per_click, experience, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            userId,
                            telegramId,
                            userData.username || 'User',
                            userData.first_name || '',
                            userData.last_name || '',
                            userData.coins || 0,
                            userData.clicks || 0,
                            userData.level || 1,
                            userData.multiplier || 1.0,
                            userData.perClick || 1,
                            userData.experience || 0,
                            now,
                            now
                        ],
                        (err) => {
                            if (err) reject(err);
                            else resolve();
                        }
                    );
                }
            }
        );
    });
}

// Загрузка пользователя из БД
async function loadUserFromDB(telegramId) {
    return new Promise((resolve, reject) => {
        db.get(
            `SELECT * FROM users WHERE telegram_id = ?`,
            [telegramId],
            (err, user) => {
                if (err) {
                    reject(err);
                    return;
                }
                
                if (user) {
                    resolve({
                        id: user.id,
                        coins: user.coins,
                        clicks: user.clicks,
                        level: user.level,
                        multiplier: user.multiplier,
                        perClick: user.per_click || 1,
                        experience: user.experience || 0,
                        username: user.username,
                        first_name: user.first_name,
                        last_name: user.last_name,
                        created_at: user.created_at
                    });
                } else {
                    // Новый пользователь
                    resolve({
                        coins: 0,
                        clicks: 0,
                        level: 1,
                        multiplier: 1.0,
                        perClick: 1,
                        experience: 0,
                        username: 'User'
                    });
                }
            }
        );
    });
}

// ============ ТЕЛЕГРАМ БОТ (ПАМЯТЬ) ============
const userData = new Map();

// Получение пользователя (с загрузкой из БД)
async function getUser(userId, ctx = null) {
    if (!userData.has(userId)) {
        try {
            const dbUser = await loadUserFromDB(userId);
            userData.set(userId, {
                coins: dbUser.coins,
                clicks: dbUser.clicks,
                level: dbUser.level,
                multiplier: dbUser.multiplier,
                perClick: dbUser.perClick,
                experience: dbUser.experience || 0,
                lastClick: 0,
                username: dbUser.username,
                first_name: dbUser.first_name,
                last_name: dbUser.last_name
            });
            
            // Обновляем username если есть контекст
            if (ctx && ctx.from) {
                const user = userData.get(userId);
                user.username = ctx.from.username || user.username;
                user.first_name = ctx.from.first_name || user.first_name;
                user.last_name = ctx.from.last_name || user.last_name;
                await saveUserToDB(userId, user);
            }
        } catch (error) {
            console.error('Ошибка загрузки пользователя:', error);
            // Создаем нового
            userData.set(userId, {
                coins: 0,
                clicks: 0,
                level: 1,
                multiplier: 1,
                perClick: 1,
                experience: 0,
                lastClick: 0,
                username: ctx?.from?.username || 'User',
                first_name: ctx?.from?.first_name || '',
                last_name: ctx?.from?.last_name || ''
            });
        }
    }
    return userData.get(userId);
}

// Функция расчета награды
function calculateReward(user) {
    const base = 1;
    const levelBonus = Math.floor(user.level * 0.5);
    const randomBonus = Math.floor(Math.random() * 3);
    const total = (base + levelBonus + randomBonus) * user.multiplier;
    return Math.max(1, Math.floor(total));
}

// Функция проверки уровня
function checkLevelUp(user) {
    const oldLevel = user.level;
    const newLevel = Math.floor(user.clicks / 15) + 1;
    
    if (newLevel > oldLevel) {
        user.level = newLevel;
        return `🎉 **ПОВЫШЕНИЕ УРОВНЯ!** 🎉\nНовый уровень: ${newLevel}`;
    }
    return null;
}

// Главное меню для бота
function getMainMenu(userId) {
    const user = userData.get(userId);
    if (!user) return null;
    
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

// ============ ТЕЛЕГРАМ КОМАНДЫ ============

// Команда /start
bot.start(async (ctx) => {
    const user = await getUser(ctx.from.id, ctx);
    const menu = getMainMenu(ctx.from.id);
    
    if (menu) {
        await ctx.replyWithMarkdownV2(
            `🎮 Добро пожаловать в *Clicker Game*, ${ctx.from.first_name}\\!\n` +
            `Ты начинаешь с ${user.coins} монет\\.\n` +
            `*Кликай кнопку ниже и начинай зарабатывать\\!*`,
            menu.keyboard
        );
    }
});

// Обработка кликов
bot.action('click', async (ctx) => {
    const userId = ctx.from.id;
    const user = await getUser(userId, ctx);
    
    // Проверка на спам
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
    user.experience += reward;
    
    // Проверяем повышение уровня
    const levelUpMessage = checkLevelUp(user);
    
    // Сохраняем в БД
    await saveUserToDB(userId, user);
    
    // Ответ пользователю
    await ctx.answerCbQuery(`+${reward} монет! 🪙`);
    
    // Обновляем сообщение
    const menu = getMainMenu(userId);
    
    if (menu) {
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
            await ctx.replyWithMarkdown(message, menu.keyboard);
        }
    }
});

// Профиль
bot.action('profile', async (ctx) => {
    const user = await getUser(ctx.from.id, ctx);
    
    const progress = (user.clicks % 15) / 15 * 100;
    const progressBar = '█'.repeat(Math.floor(progress / 10)) + 
                       '░'.repeat(10 - Math.floor(progress / 10));
    
    await ctx.editMessageText(
        `👤 *ВАШ ПРОФИЛЬ*\n\n` +
        `💰 Монеты: *${user.coins}*\n` +
        `🏆 Уровень: *${user.level}*\n` +
        `👆 Всего кликов: *${user.clicks}*\n` +
        `⚡ Множитель: *x${user.multiplier}*\n` +
        `📊 Опыт: *${user.experience}*\n\n` +
        `📈 Прогресс до след. уровня:\n` +
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
    const user = await getUser(ctx.from.id, ctx);
    
    const upgrades = [
        {
            id: 'multiplier_2',
            name: '⚡ Множитель x2',
            price: 50,
            description: 'Удваивает награду за каждый клик'
        },
        {
            id: 'multiplier_3',
            name: '🔥 Множитель x3',
            price: 150,
            description: 'Утраивает награду за каждый клик'
        },
        {
            id: 'bonus_10',
            name: '🎁 Бонус +10 монет',
            price: 30,
            description: 'Мгновенно добавляет 10 монет'
        },
        {
            id: 'level_up',
            name: '🚀 Повышение уровня',
            price: 200,
            description: 'Мгновенно повышает уровень на 1'
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
    const user = await getUser(ctx.from.id, ctx);
    
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
    
    // Сохраняем в БД
    await saveUserToDB(ctx.from.id, user);
    
    await ctx.answerCbQuery(`✅ Куплено: ${upgrade.name}`);
    
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
    try {
        const topUsers = await new Promise((resolve, reject) => {
            db.all(
                `SELECT username, coins, level, clicks 
                 FROM users 
                 ORDER BY coins DESC 
                 LIMIT 10`,
                (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                }
            );
        });
        
        let topText = `🏆 *ТОП 10 ИГРОКОВ*\n\n`;
        
        if (topUsers.length === 0) {
            topText += `Пока никого нет. Будь первым!`;
        } else {
            topUsers.forEach((user, index) => {
                const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
                topText += `${medal} ${user.username || 'Игрок'}: *${user.coins}* монет (Ур. ${user.level})\n`;
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
    } catch (error) {
        console.error('Ошибка загрузки топа:', error);
        await ctx.editMessageText(
            '❌ Не удалось загрузить топ игроков',
            Markup.inlineKeyboard([
                [Markup.button.callback('🔙 На главную', 'back')]
            ])
        );
    }
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
        `• Прогресс сохраняется\n` +
        `• Нет ограничений по времени\n\n` +
        `*Команды:*\n` +
        `/start - начать игру\n` +
        `/menu - открыть меню\n` +
        `/stats - ваша статистика\n` +
        `/bonus - секретный бонус (+100 монет)\n\n` +
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
    if (menu) {
        await ctx.editMessageText(menu.text, {
            parse_mode: 'Markdown',
            ...menu.keyboard
        });
    }
});

// Команда /menu
bot.command('menu', async (ctx) => {
    const menu = getMainMenu(ctx.from.id);
    if (menu) {
        await ctx.replyWithMarkdown(menu.text, menu.keyboard);
    }
});

// Команда /stats
bot.command('stats', async (ctx) => {
    const user = await getUser(ctx.from.id, ctx);
    await ctx.replyWithMarkdown(
        `📊 *ВАША СТАТИСТИКА*\n\n` +
        `💰 Монеты: *${user.coins}*\n` +
        `🏆 Уровень: *${user.level}*\n` +
        `👆 Всего кликов: *${user.clicks}*\n` +
        `⚡ Множитель: *x${user.multiplier}*\n` +
        `📊 Опыт: *${user.experience}*\n\n` +
        `_Продолжай в том же духе!_`
    );
});

// Команда /bonus
bot.command('bonus', async (ctx) => {
    const user = await getUser(ctx.from.id, ctx);
    const bonus = 100;
    user.coins += bonus;
    
    await saveUserToDB(ctx.from.id, user);
    
    await ctx.replyWithMarkdown(
        `🎁 *СЕКРЕТНЫЙ БОНУС!*\n\n` +
        `Вы получили: *+${bonus}* монет!\n` +
        `💰 Теперь у вас: *${user.coins}* монет\n\n` +
        `_Удачи в игре!_ 🍀`
    );
});

// Обработка ошибок бота
bot.catch((err, ctx) => {
    console.error('❌ Ошибка бота:', err);
    if (ctx.updateType === 'callback_query') {
        ctx.answerCbQuery('⚠️ Произошла ошибка. Попробуйте снова.');
    }
});

// ============ API ДЛЯ MINI APP ============

// Статические файлы
app.use(express.static('public'));

// Главная страница Mini App
app.get('/', (req, res) => {
    const htmlPath = path.join(__dirname, 'public', 'index.html');
    
    if (fs.existsSync(htmlPath)) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.setHeader('X-Frame-Options', 'ALLOWALL');
        res.sendFile(htmlPath);
    } else {
        // Временная страница
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Telegram Clicker</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://telegram.org/js/telegram-web-app.js"></script>
                <style>
                    body { 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px 20px;
                        margin: 0;
                        min-height: 100vh;
                    }
                    h1 { font-size: 28px; margin-bottom: 20px; }
                    button {
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 20px 40px;
                        font-size: 24px;
                        border-radius: 10px;
                        cursor: pointer;
                        margin-top: 30px;
                    }
                </style>
            </head>
            <body>
                <h1>🎮 Telegram Clicker Mini App</h1>
                <p>Frontend в разработке...</p>
                <button onclick="alert('Бот работает!')">Тест</button>
                <script>
                    const tg = window.Telegram.WebApp;
                    tg.expand();
                    tg.ready();
                </script>
            </body>
            </html>
        `);
    }
});

// API: Получение данных пользователя
app.get('/api/user-data', async (req, res) => {
    const telegramId = req.query.userId || req.query.tgid;
    
    if (!telegramId) {
        return res.status(400).json({ error: 'Не указан userId' });
    }
    
    try {
        const user = await loadUserFromDB(telegramId);
        res.json({
            coins: user.coins,
            clicks: user.clicks,
            level: user.level,
            multiplier: user.multiplier,
            perClick: user.perClick,
            experience: user.experience,
            username: user.username
        });
    } catch (error) {
        console.error('Ошибка загрузки пользователя:', error);
        res.status(500).json({ error: 'Ошибка сервера' });
    }
});

// API: Сохранение данных
app.post('/api/save-data', async (req, res) => {
    const { coins, clicks, level, multiplier, perClick, experience, userId } = req.body;
    
    if (!userId) {
        return res.status(400).json({ error: 'Не указан userId' });
    }
    
    try {
        await saveUserToDB(userId, {
            coins: coins || 0,
            clicks: clicks || 0,
            level: level || 1,
            multiplier: multiplier || 1,
            perClick: perClick || 1,
            experience: experience || 0
        });
        
        res.json({ success: true });
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        res.status(500).json({ error: 'Ошибка сохранения' });
    }
});

// API: Получение улучшений
app.get('/api/upgrades', (req, res) => {
    const upgrades = [
        { 
            id: 1, 
            name: '⚡ Множитель x2', 
            price: 50, 
            description: 'Удваивает доход за клик',
            type: 'multiplier', 
            value: 2 
        },
        { 
            id: 2, 
            name: '🚀 Авто-кликер', 
            price: 100, 
            description: '+1 монета каждые 10 сек',
            type: 'autoclick', 
            value: 1 
        },
        { 
            id: 3, 
            name: '💎 Усиленный клик', 
            price: 75, 
            description: '+2 к базовому доходу',
            type: 'perClick', 
            value: 2 
        },
        { 
            id: 4, 
            name: '🔥 Множитель x3', 
            price: 200, 
            description: 'Утраивает доход за клик',
            type: 'multiplier', 
            value: 3 
        },
        { 
            id: 5, 
            name: '🌟 Премиум пакет', 
            price: 300, 
            description: 'Все улучшения + бонус',
            type: 'premium', 
            value: 5 
        }
    ];
    
    res.json(upgrades);
});

// API: Покупка улучшения
app.post('/api/buy-upgrade', async (req, res) => {
    const { userId, upgradeId } = req.body;
    
    if (!userId || !upgradeId) {
        return res.status(400).json({ error: 'Не указаны userId или upgradeId' });
    }
    
    try {
        const user = await loadUserFromDB(userId);
        const upgrades = [
            { id: 1, price: 50, type: 'multiplier', value: 2 },
            { id: 2, price: 100, type: 'autoclick', value: 1 },
            { id: 3, price: 75, type: 'perClick', value: 2 },
            { id: 4, price: 200, type: 'multiplier', value: 3 },
            { id: 5, price: 300, type: 'premium', value: 5 }
        ];
        
        const upgrade = upgrades.find(u => u.id === upgradeId);
        
        if (!upgrade) {
            return res.status(400).json({ error: 'Улучшение не найдено' });
        }
        
        if (user.coins < upgrade.price) {
            return res.status(400).json({ error: 'Недостаточно монет' });
        }
        
        // Применяем улучшение
        user.coins -= upgrade.price;
        
        switch (upgrade.type) {
            case 'multiplier':
                user.multiplier *= upgrade.value;
                break;
            case 'perClick':
                user.perClick += upgrade.value;
                break;
            case 'autoclick':
                user.multiplier += 0.5;
                break;
            case 'premium':
                user.multiplier = 3;
                user.perClick = 5;
                user.coins += 100;
                break;
        }
        
        // Сохраняем
        await saveUserToDB(userId, user);
        
        res.json({ 
            success: true, 
            coins: user.coins,
            multiplier: user.multiplier,
            perClick: user.perClick
        });
        
    } catch (error) {
        console.error('Ошибка покупки:', error);
        res.status(500).json({ error: 'Ошибка сервера' });
    }
});

// API: Топ игроков для Mini App
app.get('/api/leaderboard', (req, res) => {
    db.all(
        `SELECT username, coins, level, clicks 
         FROM users 
         ORDER BY coins DESC 
         LIMIT 10`,
        (err, rows) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            res.json(rows);
        }
    );
});

// Health check для Render
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        time: new Date().toISOString(),
        service: 'telegram-clicker',
        version: '1.0.0'
    });
});

// ============ ЗАПУСК СЕРВЕРА ============

// Вебхук для бота
app.use(bot.webhookCallback('/webhook'));

app.listen(PORT, () => {
    console.log(`🚀 Сервер запущен на порту ${PORT}`);
    
    // Установка вебхука
    if (process.env.RENDER_EXTERNAL_URL) {
        const webhookUrl = `${process.env.RENDER_EXTERNAL_URL}/webhook`;
        bot.telegram.setWebhook(webhookUrl)
            .then(() => console.log(`✅ Webhook установлен: ${webhookUrl}`))
            .catch(err => console.error('❌ Ошибка установки webhook:', err));
    } else {
        // Локальная разработка
        bot.launch()
            .then(() => console.log('🤖 Бот запущен в режиме разработки'))
            .catch(err => console.error('❌ Ошибка запуска бота:', err));
    }
    
    console.log('🌐 Mini App доступен по адресу: /');
    console.log('📊 API endpoints:');
    console.log('  GET  /api/user-data?userId=ID');
    console.log('  POST /api/save-data');
    console.log('  GET  /api/upgrades');
    console.log('  POST /api/buy-upgrade');
    console.log('  GET  /api/leaderboard');
    console.log('  GET  /health');
});

// Элегантное завершение
process.once('SIGINT', () => {
    console.log('\n🛑 Остановка бота...');
    bot.stop('SIGINT');
    db.close();
    process.exit(0);
});

process.once('SIGTERM', () => {
    console.log('\n🛑 Завершение работы...');
    bot.stop('SIGTERM');
    db.close();
    process.exit(0);
});
