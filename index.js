const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

document.querySelectorAll('.topic-item').forEach(item => {
  item.addEventListener('click', () => {
    const target = item.dataset.screen;
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(target).classList.add('active');
    
    // Снимаем активность с нижнего меню при переходе в тему
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  });
});

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.screen;
    
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(target).classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});

document.querySelectorAll('#backBtn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelector('.nav-btn[data-screen="home"]').click();
  });
});

// Кнопка "Оператор" — можно привязать к tg.openTelegramLink или просто текст
document.querySelector('.operator-btn').addEventListener('click', () => {
  tg.showAlert('Связь с оператором: напишите @Operator в чате');
  // Или: tg.openTelegramLink('https://t.me/Operator');
});
