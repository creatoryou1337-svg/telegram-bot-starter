const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors({ origin: '*' })); // для теста; в проде замени на конкретный домен фронта

// Проверка, что сервер живой
app.get('/', (req, res) => {
  res.send('Backend RedWallet-style работает. Курс USDT/RUB с CoinGecko.');
});

// Получение актуального курса USDT → RUB
async function getUsdtRubRate() {
  try {
    const { data } = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=rub',
      { timeout: 6000 }
    );
    const rate = data.tether?.rub;
    return rate && rate > 10 ? rate : 95;
  } catch (e) {
    console.error('CoinGecko error:', e.message);
    return 95; // fallback
  }
}

// Эндпоинт создания заявки на вывод
app.post('/api/create-order', async (req, res) => {
  try {
    const { amountToken, cardNumber } = req.body;

    if (!amountToken || amountToken <= 0 || !cardNumber) {
      return res.status(400).json({ error: 'Укажите сумму > 0 и номер карты/СБП' });
    }

    const marketRate = await getUsdtRubRate();
    const commissionPercent = 2.5;
    const effectiveRate = marketRate * (1 - commissionPercent / 100);
    const amountRub = Math.floor(amountToken * effectiveRate);

    res.json({
      success: true,
      marketRate: marketRate.toFixed(2),
      effectiveRate: effectiveRate.toFixed(2),
      commission: `${commissionPercent}%`,
      amountRub,
      message: `Заявка на вывод ${amountToken} USDT → ${amountRub} ₽ на ${cardNumber}`,
      note: 'Тестовая версия. Средства не выводятся.'
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Внутренняя ошибка сервера' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});
