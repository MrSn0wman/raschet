// Общая логика интерфейса, не связанная с конкретным калькулятором

// Формат чисел с разделителями разрядов — объявлено сразу (не внутри DOMContentLoaded),
// потому что скрипты калькуляторов вызывают эти функции синхронно при загрузке страницы,
// раньше, чем успевает сработать событие DOMContentLoaded.
window.formatMoney = (value) => {
  if (isNaN(value)) return '—';
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(value);
};
window.formatMoney2 = (value) => {
  if (isNaN(value)) return '—';
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(value);
};

document.addEventListener('DOMContentLoaded', () => {

  // Мобильное меню (гамбургер)
  const toggle = document.getElementById('nav-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  if (toggle && mobileNav){
    toggle.addEventListener('click', () => {
      const isOpen = mobileNav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  }

  // Выпадающие меню шапки: клик/тап открывает и закрывает (для сенсорных экранов),
  // hover уже работает через CSS на десктопе
  document.querySelectorAll('.nav-drop-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const panel = btn.nextElementSibling;
      const willOpen = !panel.classList.contains('force-open');
      document.querySelectorAll('.nav-drop-panel.force-open').forEach(p => p.classList.remove('force-open'));
      document.querySelectorAll('.nav-drop-btn').forEach(b => b.setAttribute('aria-expanded', 'false'));
      if (willOpen){
        panel.classList.add('force-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.nav-drop-panel.force-open').forEach(p => p.classList.remove('force-open'));
    document.querySelectorAll('.nav-drop-btn').forEach(b => b.setAttribute('aria-expanded', 'false'));
  });

  // Поиск по калькуляторам на главной
  const finder = document.getElementById('finder-input');
  if (finder){
    finder.addEventListener('keydown', (e) => {
      if (e.key === 'Enter'){
        const q = finder.value.trim().toLowerCase();
        const map = {
          'площад': 'calc-area.html',
          'объем': 'calc-volume.html',
          'объём': 'calc-volume.html',
          'процент': 'calc-percent.html',
          'ипотек': 'calc-mortgage.html',
          'кредит': 'calc-mortgage.html',
          'вклад': 'calc-deposit.html',
          'депозит': 'calc-deposit.html',
          'имт': 'calc-bmi.html',
          'вес': 'calc-bmi.html'
        };
        const key = Object.keys(map).find(k => q.includes(k));
        if (key) window.location.href = map[key];
      }
    });
  }
});
