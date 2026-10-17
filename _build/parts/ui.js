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

// Форматирование ЦЕЛЫХ чисел разрядами прямо в поле ввода (для сумм в рублях),
// с сохранением позиции курсора. Дробная часть не поддерживается намеренно —
// суммы кредитов/вкладов вводятся целыми рублями.
window.formatThousandsRaw = (digitsOnly) => {
  let intPart = digitsOnly.replace(/^0+(?=\d)/, '');
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
};

window.attachThousandsInput = (el) => {
  el.type = 'text';
  el.setAttribute('inputmode', 'numeric');
  if (el.value){
    el.value = formatThousandsRaw(String(el.value).replace(/\D/g, ''));
  }
  el.addEventListener('input', () => {
    const start = el.selectionStart ?? el.value.length;
    const oldVal = el.value;
    const digitsBeforeCursor = oldVal.slice(0, start).replace(/\D/g, '').length;

    const digitsOnly = oldVal.replace(/\D/g, '');
    const newVal = formatThousandsRaw(digitsOnly);
    el.value = newVal;

    let count = 0, pos = newVal.length;
    if (digitsBeforeCursor === 0){
      pos = 0;
    } else {
      for (let idx = 0; idx < newVal.length; idx++){
        if (/\d/.test(newVal[idx])) count++;
        if (count === digitsBeforeCursor){ pos = idx + 1; break; }
      }
    }
    if (el.setSelectionRange) el.setSelectionRange(pos, pos);
  });
};

window.parseFormattedNumber = (el) => {
  if (!el) return NaN;
  const raw = String(el.value).replace(/\D/g, '');
  return raw === '' ? NaN : parseFloat(raw);
};

// «Умное» форматирование с адаптивной точностью — для площади/объёма, где выбор
// единицы измерения (мм/см/м/км) может дать как очень маленькие, так и очень
// большие числа. Обычный formatMoney2 (фикс. 2 знака) обнулял мелкие результаты.
window.formatSmart = (value) => {
  if (isNaN(value)) return '—';
  if (value === 0) return '0';
  const abs = Math.abs(value);
  let decimals;
  if (abs >= 1000) decimals = 0;
  else if (abs >= 1) decimals = 2;
  else if (abs >= 0.01) decimals = 4;
  else if (abs >= 0.0001) decimals = 6;
  else decimals = 8;
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: decimals }).format(value);
};

// Базовый URL бэкенда. Пустая строка = бэкенд не настроен: вызовы тихо отключаются,
// сайт работает в полностью автономном режиме (деградация по контракту из README бэкенда).
window.RASCHET_API_BASE = window.RASCHET_API_BASE || '';

// Тост-уведомление (один на страницу, переиспользуется)
window.showToast = (text) => {
  let t = document.querySelector('.toast');
  if (!t){
    t = document.createElement('div');
    t.className = 'toast';
    t.setAttribute('role', 'status');
    document.body.appendChild(t);
  }
  t.textContent = text;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 2200);
};

// Буфер обмена с фолбэком
window.copyText = (text, okMessage) => {
  const done = () => window.showToast(okMessage || 'Скопировано');
  if (navigator.clipboard && window.isSecureContext){
    navigator.clipboard.writeText(text).then(done).catch(() => window.copyTextFallback(text, done));
  } else {
    window.copyTextFallback(text, done);
  }
};
window.copyTextFallback = (text, done) => {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.setAttribute('readonly', '');
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch (e) {}
  document.body.removeChild(ta);
  done();
};

// Отправка события своей аналитике; никогда не бросает и не влияет на UX.
window.trackEvent = (type, page, meta) => {
  if (!window.RASCHET_API_BASE) return;
  try{
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 3000);
    fetch(window.RASCHET_API_BASE + '/api/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: type, page: page, meta: meta || null }),
      signal: ctrl.signal,
      keepalive: true
    }).catch(() => {});
  } catch (e) {}
};

document.addEventListener('DOMContentLoaded', () => {

  // Переключатель темы (светлая/тёмная). Выбор хранится в localStorage;
  // при отсутствии выбора тема следует за системной (см. init-скрипт в <head>).
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle){
    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('raschet-theme', next); } catch (e) {}
    });
  }

  // Мобильное меню (гамбургер)
  const toggle = document.getElementById('nav-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  if (toggle && mobileNav){
    toggle.addEventListener('click', () => {
      const isOpen = mobileNav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      toggle.setAttribute('aria-label', isOpen ? 'Закрыть меню' : 'Открыть меню');
    });
  }

  // Категории в шапке: hover с задержкой намерения, эксклюзивно,
  // клик — для тача/клавиатуры; уход курсора закрывает.
  const navCats = document.querySelectorAll('.nav-cat');
  let openTimer = null;
  let closeTimer = null;
  const closeNavCats = () => {
    navCats.forEach((c) => {
      c.classList.remove('open');
      const b = c.querySelector('.nav-cat-btn');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  };
  navCats.forEach((cat) => {
    const btn = cat.querySelector('.nav-cat-btn');
    cat.addEventListener('mouseenter', () => {
      clearTimeout(closeTimer);
      clearTimeout(openTimer);
      openTimer = setTimeout(() => {
        closeNavCats();
        cat.classList.add('open');
        if (btn) btn.setAttribute('aria-expanded', 'true');
      }, 120);
    });
    cat.addEventListener('mouseleave', () => {
      clearTimeout(openTimer);
      closeTimer = setTimeout(() => {
        cat.classList.remove('open');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      }, 200);
    });
    if (btn){
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearTimeout(openTimer);
        clearTimeout(closeTimer);
        const isOpen = cat.classList.contains('open');
        if (!isOpen){
          // панель закрыта: открываем, не переходя по ссылке (переход — по второму клику)
          e.preventDefault();
          closeNavCats();
          cat.classList.add('open');
          btn.setAttribute('aria-expanded', 'true');
        } else {
          // панель открыта: <a> перейдёт в раздел каталога, «Ещё»-кнопка просто закроется
          closeNavCats();
        }
      });
    }
    // клавиатура: фокус внутри категории открывает её
    cat.addEventListener('focusin', () => {
      clearTimeout(closeTimer);
      if (!cat.classList.contains('open')){
        closeNavCats();
        cat.classList.add('open');
        if (btn) btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest || !e.target.closest('.nav-cat')) closeNavCats();
  });

  // Избранное (localStorage): бейдж, панель, звезда на страницах калькуляторов
  const FAV_KEY = 'raschet-favs';
  const RECENT_KEY = 'raschet-recent';
  const readList = (key) => {
    try { return JSON.parse(localStorage.getItem(key) || '[]') || []; } catch (e) { return []; }
  };
  const writeList = (key, list) => {
    try { localStorage.setItem(key, JSON.stringify(list)); } catch (e) {}
  };
  const favBtn = document.getElementById('fav-btn');
  const favPanel = document.getElementById('fav-panel');
  const favBadge = document.getElementById('fav-badge');
  const favList = document.getElementById('fav-list');
  const favEmpty = document.getElementById('fav-empty');

  const renderFavBadge = () => {
    if (!favBadge) return;
    const n = readList(FAV_KEY).length;
    favBadge.hidden = n === 0;
    favBadge.textContent = n;
  };
  const renderFavPanel = () => {
    if (!favList || !favEmpty) return;
    const favs = readList(FAV_KEY);
    favList.innerHTML = '';
    favs.forEach((item) => {
      const a = document.createElement('a');
      a.href = item.href;
      a.textContent = item.title;
      favList.appendChild(a);
    });
    favEmpty.hidden = favs.length > 0;
  };
  const closeFav = () => {
    if (!favPanel || favPanel.hidden) return;
    favPanel.hidden = true;
    if (favBtn) favBtn.setAttribute('aria-expanded', 'false');
  };
  if (favBtn && favPanel){
    favBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const willOpen = favPanel.hidden;
      closeNavCats();
      if (willOpen) renderFavPanel();
      favPanel.hidden = !willOpen;
      favBtn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });
    favPanel.addEventListener('click', (e) => { e.stopPropagation(); });
  }
  renderFavBadge();

  // Страница калькулятора: <body data-calc-slug="…" data-calc-title="…">
  const calcSlug = document.body.getAttribute('data-calc-slug');
  const calcTitle = document.body.getAttribute('data-calc-title');
  if (calcSlug && calcTitle){
    // недавние
    const recent = readList(RECENT_KEY).filter((i) => i.slug !== calcSlug);
    recent.unshift({ slug: calcSlug, title: calcTitle, href: location.pathname.split('/').pop() || 'index.html' });
    writeList(RECENT_KEY, recent.slice(0, 8));

    // звезда избранного
    const favToggle = document.getElementById('fav-toggle');
    if (favToggle){
      const syncFavBtn = () => {
        const isFav = readList(FAV_KEY).some((i) => i.slug === calcSlug);
        favToggle.classList.toggle('is-fav', isFav);
        favToggle.setAttribute('aria-pressed', isFav ? 'true' : 'false');
        favToggle.querySelector('span').textContent = isFav ? 'В избранном' : 'В избранное';
      };
      favToggle.addEventListener('click', () => {
        let favs = readList(FAV_KEY);
        if (favs.some((i) => i.slug === calcSlug)){
          favs = favs.filter((i) => i.slug !== calcSlug);
          window.showToast('Убрано из избранного');
        } else {
          favs.push({ slug: calcSlug, title: calcTitle, href: location.pathname.split('/').pop() });
          window.showToast('Добавлено в избранное');
        }
        writeList(FAV_KEY, favs);
        renderFavBadge();
        syncFavBtn();
      });
      syncFavBtn();
    }

    // аналитика: просмотр + первый запуск расчёта
    window.trackEvent('view', calcSlug);
    let calcTracked = false;
    document.querySelectorAll('.calc-card input, .calc-card select, .calc-card textarea').forEach((el) => {
      el.addEventListener('input', () => {
        if (!calcTracked){ calcTracked = true; window.trackEvent('calc', calcSlug); }
      }, { once: false });
    });
  }

  // Глобальные закрытия: клик мимо и Esc
  document.addEventListener('click', () => { closeNavCats(); closeFav(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape'){
      closeNavCats();
      closeFav();
      if (mobileNav && mobileNav.classList.contains('open')){
        mobileNav.classList.remove('open');
        if (toggle){
          toggle.setAttribute('aria-expanded', 'false');
          toggle.setAttribute('aria-label', 'Открыть меню');
          toggle.focus();
        }
      }
    }
  });

  // Экшены калькулятора: поделиться / копировать / печать.
  // Поля, попадающие в ссылку, помечены data-share="paramName".
  const shareBtn = document.getElementById('share-btn');
  if (shareBtn){
    // восстановить состояние из URL при загрузке
    const params = new URLSearchParams(location.search);
    let restored = false;
    document.querySelectorAll('[data-share]').forEach((el) => {
      const name = el.getAttribute('data-share');
      if (params.has(name)){
        el.value = params.get(name);
        restored = true;
      }
    });
    if (restored){
      const first = document.querySelector('[data-share]');
      if (first) first.dispatchEvent(new Event('input', { bubbles: true }));
    }
    shareBtn.addEventListener('click', () => {
      const p = new URLSearchParams();
      document.querySelectorAll('[data-share]').forEach((el) => {
        p.set(el.getAttribute('data-share'), String(el.value).replace(/\s/g, ''));
      });
      const url = location.origin + location.pathname + '?' + p.toString();
      window.copyText(url, 'Ссылка на расчёт скопирована');
    });
  }

  const copyBtn = document.getElementById('copy-btn');
  if (copyBtn){
    copyBtn.addEventListener('click', () => {
      const target = document.querySelector(copyBtn.getAttribute('data-copy-target') || '.result-panel .r-value');
      const label = document.querySelector('.result-panel .r-label');
      if (target){
        const text = (label ? label.textContent + ': ' : '') + target.textContent;
        window.copyText(text, 'Результат скопирован');
      }
    });
  }

  const printBtn = document.getElementById('print-btn');
  if (printBtn){
    printBtn.addEventListener('click', () => window.print());
  }

  // «Популярное» на главной: пробуем свою аналитику, иначе остаётся статичный дефолт из HTML
  const popStrip = document.getElementById('popular-strip');
  if (popStrip && window.RASCHET_API_BASE){
    try{
      const ctrl = new AbortController();
      setTimeout(() => ctrl.abort(), 3000);
      fetch(window.RASCHET_API_BASE + '/api/popular?limit=10', { signal: ctrl.signal })
        .then((r) => r.ok ? r.json() : null)
        .then((data) => {
          if (!data || !data.items || !data.items.length) return;
          popStrip.innerHTML = '';
          data.items.forEach((item, idx) => {
            // href принимаем только относительный (защита от javascript:-URL при компрометации API)
            if (!item || typeof item.href !== 'string' || !/^[a-z0-9][a-z0-9\-\/\.]*$/i.test(item.href)) return;
            const a = document.createElement('a');
            a.className = 'pop-item';
            a.href = item.href;
            const n = document.createElement('span');
            n.className = 'pop-n';
            n.textContent = idx + 1;
            a.appendChild(n);
            a.appendChild(document.createTextNode(item.title));
            popStrip.appendChild(a);
          });
        })
        .catch(() => {});
    } catch (e) {}
  }

  // Поиск по калькуляторам на главной.
  // Ключи проверяются от более длинных к более коротким, чтобы «автокредит»
  // не перехватывался ключом «кредит», а «идеальный вес» — ключом «вес».
  const finder = document.getElementById('finder-input');
  if (finder){
    const runFinder = () => {
      const q = finder.value.trim().toLowerCase();
      if (!q) return;
      const map = {
        'площад': 'calc-area.html',
        'объем': 'calc-volume.html',
        'объём': 'calc-volume.html',
        'процент': 'calc-percent.html',
        'ипотек': 'calc-mortgage.html',
        'досрочн': 'calc-mortgage-early.html',
        'кредит': 'calc-credit.html',
        'вклад': 'calc-deposit.html',
        'депозит': 'calc-deposit.html',
        'имт': 'calc-bmi.html',
        'вес': 'calc-weight.html',
        'вычет': 'calc-tax-deduction.html',
        'транспортный налог': 'calc-transport-tax.html',
        'налог на авто': 'calc-transport-tax.html',
        'расход топлива': 'calc-fuel.html',
        'бензин': 'calc-fuel.html',
        'стаж': 'calc-work-experience.html',
        'отпускные дни': 'calc-vacation-days.html',
        'отпускные': 'calc-vacation-pay.html',
        'автокредит': 'calc-car-loan.html',
        'рефинансирование': 'calc-refinancing.html',
        'микрозайм': 'calc-microloan.html',
        'займ': 'calc-loan-interest.html',
        'заём': 'calc-loan-interest.html',
        'пени': 'calc-penalty-tax.html',
        'неустойка': 'calc-penalty-contract.html',
        '395 гк': 'calc-art395.html',
        'дду': 'calc-penalty-ddu.html',
        'дольщик': 'calc-penalty-ddu.html',
        'нод': 'calc-gcd.html',
        'нок': 'calc-lcm.html',
        'множители': 'calc-factorization.html',
        'степень': 'calc-power.html',
        'корень': 'calc-power.html',
        'дроби': 'calc-fractions.html',
        'система счисления': 'calc-number-base.html',
        'двоичная': 'calc-number-base.html',
        'дни': 'calc-days.html',
        'возраст': 'calc-age.html',
        'скидка': 'calc-discount.html',
        'идеальный вес': 'calc-weight.html',
        'электромобиль': 'calc-ev-charging.html',
        'зарядка': 'calc-ev-charging.html',
        'случайное число': 'calc-random-number.html',
        'рандом': 'calc-random-number.html',
        'выбор из списка': 'calc-random-pick.html',
        'перемешать': 'calc-shuffle-list.html',
        'разделить на группы': 'calc-split-groups.html',
        'сравнение списков': 'calc-compare-lists.html',
        'пароль': 'calc-password-generator.html',
        'промокод': 'calc-promo-generator.html',
        'qr': 'calc-qr-generator.html',
        'qr-код': 'calc-qr-generator.html',
        'ндс': 'calc-vat.html',
        'самозанятые': 'calc-samozanyaty.html',
        'нпд': 'calc-samozanyaty.html',
        'осаго': 'calc-osago.html',
        'страховка авто': 'calc-osago.html',
        'растаможка': 'calc-customs-clearance.html',
        'утильсбор': 'calc-recycling-fee.html',
        'утилизационный сбор': 'calc-recycling-fee.html',
        'сумма прописью': 'calc-amount-in-words.html',
        'число прописью': 'calc-amount-in-words.html',
        'доли в квартире': 'calc-shares-apartment.html',
        'маткапитал': 'calc-maternal-capital-shares.html',
        'материнский капитал': 'calc-maternal-capital-shares.html',
        'страховые взносы': 'calc-insurance-contributions.html',
        'взносы ип': 'calc-insurance-contributions.html',
        'конвертер единиц': 'calc-unit-converter.html',
        'чаевые': 'calc-tip.html',
        'часовые пояса': 'calc-timezone.html',
        'сложный процент': 'calc-compound-interest.html',
        'больничный': 'calc-sick-leave.html',
        'декретные': 'calc-maternity-leave.html',
        'беременность и родам': 'calc-maternity-leave.html',
        'пенсия': 'calc-pension.html',
        'пенсионный балл': 'calc-pension.html',
        'ипк': 'calc-pension.html',
        'иис': 'calc-iis.html',
        'индивидуальный инвестиционный счет': 'calc-iis.html',
        'отпуск': 'calc-vacation-days.html',
        'ндфл': 'calc-ndfl.html',
        'налог с продажи': 'calc-property-sale-tax.html',
        'продаж': 'calc-property-sale-tax.html',
        'валют': 'calc-currency.html',
        'конвертер валют': 'calc-currency.html',
        'доллар': 'calc-currency.html',
        'евро': 'calc-currency.html',
        'счетчик слов': 'calc-word-counter.html',
        'счётчик слов': 'calc-word-counter.html',
        'транслит': 'calc-translit.html',
        'дубл': 'calc-dedupe-lines.html',
        'инн': 'calc-inn.html',
        'снилс': 'calc-snils.html',
        'номер карты': 'calc-bank-card.html',
        'uuid': 'calc-uuid.html',
        'lorem': 'calc-lorem.html',
        'лорем': 'calc-lorem.html',
        'никнейм': 'calc-nickname.html',
        'unix': 'calc-unix-time.html',
        'таймстамп': 'calc-unix-time.html',
        'рабочие дни': 'calc-workdays.html',
        'отсчёт': 'calc-countdown.html',
        'отсчет': 'calc-countdown.html'
      };
      const key = Object.keys(map)
        .sort((a, b) => b.length - a.length)
        .find(k => q.includes(k));
      if (key) window.location.href = map[key];
    };
    finder.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') runFinder();
    });
    const finderBtn = document.getElementById('finder-btn');
    if (finderBtn) finderBtn.addEventListener('click', runFinder);
  }
});
