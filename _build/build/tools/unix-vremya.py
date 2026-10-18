# -*- coding: utf-8 -*-
# Unix timestamp ↔ дата/время: живой тикер, двусторонняя конвертация.

TOOL = {
  "slug": "unix-vremya",
  "title": "Unix timestamp",
  "meta_title": "Unix timestamp онлайн — конвертер в дату и обратно",
  "meta_desc": "Текущее Unix-время в реальном времени, перевод timestamp в дату (секунды и миллисекунды определяются сами) и даты в timestamp. UTC и локальный пояс.",
  "h1": "Unix-время: timestamp ↔ дата",
  "sub": "Живое текущее время в секундах Unix и перевод timestamp в дату и обратно.",
  "category": "Дата и время",
  "fields_html": """
<div class="field-grid">
  <div class="field">
    <label for="ux-ts">Timestamp → дата</label>
    <input type="text" id="ux-ts" inputmode="numeric" placeholder="1760486400" data-share="ts">
    <span class="hint">Секунды или миллисекунды — определим сами.</span>
  </div>
  <div class="field">
    <label for="ux-date">Дата → timestamp</label>
    <input type="datetime-local" id="ux-date" step="1">
  </div>
  <div class="field full">
    <label for="ux-tz">Поле «Дата → timestamp» трактовать как</label>
    <select id="ux-tz">
      <option value="local" selected>Локальное время (вашего устройства)</option>
      <option value="utc">UTC</option>
    </select>
    <div class="error-msg" id="ux-error" role="alert">Timestamp — это целое число секунд или миллисекунд.</div>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Сейчас, Unix-секунды</div>
  <div class="r-value" id="ux-now">—</div>
  <div class="r-rows">
    <div><b id="ux-now-local">—</b><span>сейчас, локальное время</span></div>
    <div><b id="ux-now-utc">—</b><span>сейчас, UTC</span></div>
    <div><b id="ux-from-ts">—</b><span>дата из timestamp (локальная / UTC)</span></div>
    <div><b id="ux-from-date">—</b><span>timestamp из даты</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Unix-время — число секунд, прошедших с 1 января 1970 года, 00:00:00 UTC (эпоха Unix). Оно не зависит от часовых поясов и високосных секунд, поэтому именно его используют в базах данных, API и логах. Большое число в верхней части страницы — текущее время, оно обновляется каждую секунду.</p>
<p>При переводе timestamp в дату формат определяется автоматически: значения по модулю от 10¹² считаются миллисекундами, меньшие — секундами. Граница выбрана так, что сегодняшние даты попадают в правильный разряд: сейчас это примерно 1,76 × 10⁹ секунд или 1,76 × 10¹² миллисекунд. Даты ранее 1970 года (отрицательный timestamp) тоже поддерживаются.</p>
<p>При переводе даты в timestamp выберите, как трактовать введённое время: как локальное время вашего устройства или как UTC. Результат показывается и в секундах, и в миллисекундах — копируйте тот формат, который ждёт ваша система. Диапазон ограничен точностью JavaScript: примерно ±285 тысяч лет от эпохи.</p>
<p>Разберём на числе. Вводите timestamp <code>1735689600</code> — конвертер видит десятизначное значение, трактует его как секунды и выдаёт 1 января 2025 года, 00:00:00 UTC. Тот же момент в миллисекундах выглядит так:</p>
<p><code>1735689600000</code></p>
<p>Обратная операция симметрична: ставите дату 01.01.2025 00:00 и режим UTC — получаете те же <code>1735689600</code>. Если выбрать локальное время, результат сдвинется на ваше смещение: в Екатеринбурге (UTC+5) полночь первого января даст <code>1735671600</code>, то есть на 18 000 секунд меньше.</p>
<p>Если под рукой нет конвертера, timestamp можно прикинуть арифметикой: умножьте число полных дней от эпохи на 86 400 — столько секунд в сутках. Полночь 1 января 2025 года наступила через 20 089 дней после эпохи:</p>
<p><code>20089 × 86400 = 1735689600</code></p>
<h3>Секунды против миллисекунд</h3>
<p>Главный источник путаницы — разрядность. Unix-утилиты, большинство API и языки вроде Python работают в секундах, а JavaScript и Java — в миллисекундах. Если API вернул число с тремя лишними нулями, дата «уедет» на тысячи лет вперёд; если, наоборот, отбросить миллисекунды делением, проверьте, куда делся остаток, — иногда важна точность до долей секунды. Конвертер снимает вопрос: он смотрит на величину числа, сам выбирает разряд и показывает оба варианта.</p>
<h3>Часовой пояс решает всё</h3>
<p>Timestamp сам по себе не знает ни про Москву, ни про UTC — это просто счётчик. Пояс появляется только при переводе числа в читаемую дату. Поэтому один и тот же момент в разных поясах выглядит по-разному, а один и тот же «локальный полдень» в разных городах — это разные timestamp. Передаёте дату в чужую систему — договоритесь, в каком поясе трактуется время: расхождение в несколько часов почти всегда означает, что одна сторона считает в UTC, а другая — в локальном времени.</p>
<p>Ещё одна тонкость: unix-время не считает високосные секунды, которые изредка добавляют к UTC для синхронизации с вращением Земли. Каждые сутки в нём ровно 86 400 секунд, поэтому на длинных интервалах unix-время и астрономическое слегка расходятся — для бытовых и программных задач этой разницей пренебрегают.</p>
<h3>Где встречается unix-время</h3>
<p>Практически везде, где программа хранит или сравнивает моменты времени:</p>
<ul>
<li>поля created_at и updated_at в базах данных;</li>
<li>сроки действия токенов, сессий и JWT;</li>
<li>метки событий в логах и системах мониторинга;</li>
<li>заголовки кэширования и cookies в HTTP.</li>
</ul>
<p>Причина простая: целое число легко хранить, сортировать и сравнивать, а разница двух timestamp сразу даёт длительность в секундах — без календарной арифметики с месяцами разной длины. Поэтому unix-время стало универсальным форматом обмена датами между системами.</p>""",
  "faq": [
    ("Чем отличаются timestamp в секундах и миллисекундах?",
     "В миллисекундах значение в тысячу раз больше. JavaScript (Date.now) и Java используют миллисекунды, Unix-утилиты и большинство API — секунды. Конвертер определяет формат по величине числа."),
    ("Почему 1970 год называется эпохой Unix?",
     "Так решили авторы первых версий Unix: отсчёт времени в системе начался с полуночи 1 января 1970 года по UTC. Даты раньше эпохи кодируются отрицательными числами."),
    ("Что будет 19 января 2038 года?",
     "В этот день 32-битный счётчик секунд переполнится (проблема 2038 года). Современные 64-битные системы, включая этот конвертер, ей не подвержены."),
    ("Timestamp одинаковый во всём мире?",
     "Да, это абсолютное число секунд от эпохи, без часовых поясов. Различия возникают только при превращении timestamp в читаемую дату — тут и нужен выбор пояса."),
    ("Как узнать текущий timestamp?",
     "Он показан в верхней части этой страницы и обновляется каждую секунду. В коде текущее время получают через Date.now() в JavaScript, time() в PHP или time.time() в Python."),
    ("Почему конвертер показывает дату со сдвигом на несколько часов?",
     "Почти наверняка дело в часовом поясе: одна сторона трактует время как UTC, другая — как локальное. Переключите режим и сравните результаты — сдвиг совпадёт с вашим смещением от UTC."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var tsEl = document.getElementById('ux-ts');
  var dateEl = document.getElementById('ux-date');
  var tzEl = document.getElementById('ux-tz');
  var errEl = document.getElementById('ux-error');
  var nowEl = document.getElementById('ux-now');
  var nowLocalEl = document.getElementById('ux-now-local');
  var nowUtcEl = document.getElementById('ux-now-utc');
  var fromTsEl = document.getElementById('ux-from-ts');
  var fromDateEl = document.getElementById('ux-from-date');

  function pad(n){ return n < 10 ? '0' + n : '' + n; }

  function fmtLocal(ms){
    var d = new Date(ms);
    if (isNaN(d.getTime())) return '—';
    return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + d.getFullYear() + ' ' +
           pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
  }

  function fmtUtc(ms){
    var d = new Date(ms);
    if (isNaN(d.getTime())) return '—';
    return pad(d.getUTCDate()) + '.' + pad(d.getUTCMonth() + 1) + '.' + d.getUTCFullYear() + ' ' +
           pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()) + ':' + pad(d.getUTCSeconds()) + ' UTC';
  }

  function showError(msg){
    errEl.textContent = msg;
    errEl.classList.add('visible');
  }
  function hideError(){ errEl.classList.remove('visible'); }

  function tick(){
    var now = Date.now();
    nowEl.textContent = window.formatMoney(Math.floor(now / 1000));
    nowLocalEl.textContent = fmtLocal(now);
    nowUtcEl.textContent = fmtUtc(now);
  }

  function renderTs(){
    var raw = tsEl.value.replace(/[\s_]/g, '');
    if (raw === ''){ fromTsEl.textContent = '—'; hideError(); return; }
    if (!/^-?\d+$/.test(raw)){
      showError('Timestamp — это целое число секунд или миллисекунд.');
      fromTsEl.textContent = '—';
      return;
    }
    var n = parseInt(raw, 10);
    if (!isFinite(n)){
      showError('Число слишком большое для точного перевода.');
      fromTsEl.textContent = '—';
      return;
    }
    hideError();
    var ms = Math.abs(n) >= 1e12 ? n : n * 1000;
    if (isNaN(new Date(ms).getTime())){
      showError('Такой timestamp не помещается в диапазон дат JavaScript.');
      fromTsEl.textContent = '—';
      return;
    }
    fromTsEl.textContent = fmtLocal(ms) + ' / ' + fmtUtc(ms);
  }

  function renderDate(){
    var v = dateEl.value;
    if (!v){ fromDateEl.textContent = '—'; return; }
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/.exec(v);
    if (!m){ fromDateEl.textContent = '—'; return; }
    var y = +m[1], mo = +m[2] - 1, d = +m[3], h = +m[4], mi = +m[5], s = m[6] ? +m[6] : 0;
    var ms = tzEl.value === 'utc' ? Date.UTC(y, mo, d, h, mi, s) : new Date(y, mo, d, h, mi, s).getTime();
    fromDateEl.textContent = window.formatMoney(Math.floor(ms / 1000)) + ' с (' + window.formatMoney(ms) + ' мс)';
  }

  tsEl.addEventListener('input', renderTs);
  dateEl.addEventListener('input', renderDate);
  tzEl.addEventListener('change', renderDate);
  tick();
  setInterval(tick, 1000);
  renderTs();
})();
""",
  "page_css": "",
  "related": ["chasovye-poyasa", "dni", "obratnyy-otschet", "rabochie-dni"],
}
