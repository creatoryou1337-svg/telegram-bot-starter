const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors({ origin: '*' })); // Для теста — разрешаем всем; потом замени на URL фронта

// Главная для проверки
app.get('/', (req, res) => {
  res.send('Backend крипто-обменника работает! Курс USDT/RUB берётся с CoinGecko.');
});

// Функция получения курса USDT/RUB
async function getUsdtRubRate() {
  try {
    const response = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=rub',
      { timeout: 5000 }
    );
    const rate = response.data.tether.rub;
    return rate && rate > 10 ? rate : 95; // Fallback ~95 если API упал
  } catch (err) {
    console.error('CoinGecko error:', err.message);
    return 95; // Fallback
  }
}

// Эндпоинт создания заявки на вывод (без кошелька)
app.post('/api/create-order', async (req, res) => {
  const { amountToken, cardNumber } = req.body;

  if (!amountToken || amountToken <= 0 || !cardNumber) {
    return res.status(400).json({ error: 'Укажите сумму > 0 и номер карты/СБП' });
  }

  const marketRate = await getUsdtRubRate();
  const commissionPercent = 2.5;
  const commissionFactor = 1 - (commissionPercent / 100);
  const effectiveRate = marketRate * commissionFactor;
  const amountRub = Math.floor(amountToken * effectiveRate); // округляем вниз

  res.json({
    success: true,
    marketRate: marketRate.toFixed(2),
    effectiveRate: effectiveRate.toFixed(2),
    commission: `${commissionPercent}%`,
    amountRub: amountRub,
    message: `Заявка на вывод ${amountToken} USDT → ${amountRub} ₽ на ${cardNumber}`,
    note: 'Это тестовая версия — средства не выводятся. Курс реального времени с CoinGecko.'
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});
