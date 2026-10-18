# -*- coding: utf-8 -*-
# Обратный отсчёт до даты/времени с прогресс-баром от момента загрузки страницы.

TOOL = {
  "slug": "obratnyy-otschet",
  "title": "Обратный отсчёт",
  "meta_title": "Обратный отсчёт до даты онлайн — живой таймер",
  "meta_desc": "Живой таймер обратного отсчёта до любой даты и времени: дни, часы, минуты, секунды и прогресс-бар. По умолчанию — до Нового года.",
  "h1": "Обратный отсчёт до даты",
  "sub": "Живой таймер до выбранного момента: дни, часы, минуты и секунды с прогресс-баром.",
  "category": "Дата и время",
  "fields_html": """
<div class="field-grid">
  <div class="field">
    <label for="cd-target">Дата и время цели</label>
    <input type="datetime-local" id="cd-target">
    <span class="hint">Время трактуется как локальное время вашего устройства.</span>
    <div class="error-msg" id="cd-error" role="alert">Выберите дату и время цели.</div>
  </div>
  <div class="field">
    <label>Действие</label>
    <button class="btn btn-primary" id="cd-start" type="button">Запустить отсчёт</button>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">До цели осталось</div>
  <div class="r-value cd-digits" id="cd-value">—</div>
  <div class="cd-labels"><span>дней</span><span>часов</span><span>минут</span><span>секунд</span></div>
  <div class="cd-bar"><div class="cd-bar-fill" id="cd-bar"></div></div>
  <div class="r-rows cd-rows">
    <div><b id="cd-target-out">—</b><span>цель</span></div>
    <div><b id="cd-pct">—</b><span>пройдено с момента открытия страницы</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как работает обратный отсчёт</h2>
<p>Укажите дату и время цели — таймер покажет, сколько осталось дней, часов, минут и секунд, и будет обновляться каждую секунду. По умолчанию стоит ближайший Новый год. Когда момент наступит, отсчёт остановится на сообщении «Время наступило!» — отрицательных значений не бывает.</p>
<p>Механика простая: раз в секунду таймер сравнивает текущее время вашего устройства с целевым моментом и раскладывает разницу на дни, часы, минуты и секунды. Поле ввода трактуется как локальное время вашего часового пояса. Менять цель можно сколько угодно раз — отсчёт перезапускается автоматически, страницу перезагружать не нужно.</p>
<p>Прогресс-бар показывает, какая доля времени прошла с момента открытия страницы до цели: при загрузке он всегда на нуле и растёт по мере приближения к дедлайну. Это честная метрика «сколько уже выждали» за текущий сеанс, а не доля от начала времён.</p>
<p>Цель задаётся с точностью до минуты — поле принимает и дату, и время. Если выбрать момент в прошлом, таймер не пойдёт: он сразу покажет «Время наступило!» и подсказку выбрать дату в будущем. Отсчёт в прошлое бессмысленен, но так можно проверить, что дата введена правильно.</p>
<p>Остаток выводится с правильными окончаниями слов — «1 день», «2 часа», «5 минут», — так что значение легко прочитать вслух или переписать в сообщение. Когда до цели остаётся меньше суток, дни обнуляются и главными становятся часы: именно они отсчитывают последний рывок перед событием.</p>
<p>Пример: сегодня 18 октября, цель — Новый год. До полуночи 1 января остаётся примерно 74 дня, в секундах это:</p>
<p><code>74 × 86400 ≈ 6 393 600</code></p>
<p>На экране остаток выглядит как «74 дня, столько-то часов, минут и секунд», и младший разряд уменьшается каждую секунду. Если поставить цель на завтрашние 18:00, увидите остаток вроде «1 день 4 часа 12 минут» — точное значение зависит от момента, когда вы открыли страницу. Интервал почти не ограничен: поставьте цель через несколько лет — таймер честно покажет тысячу с лишним дней. Счётчик не сбрасывается при обновлении страницы, потому что вычисляется из текущего времени; сбрасывается только прогресс-бар, привязанный к сеансу.</p>
<h3>Часовой пояс имеет значение</h3>
<p>Таймер живёт в локальном времени вашего устройства. Если цель задана в другом поясе — например, старт мероприятия «в 12:00 по Москве», а вы в другом городе, — переведите момент в своё время заранее, например нашим калькулятором часовых поясов. Один и тот же физический момент в разных поясах называется по-разному, и таймер знает только то время, которое вы ввели.</p>
<h3>От чего зависит точность</h3>
<p>Отсчёт опирается на системные часы устройства: если они спешат или отстают, таймер покажет соответствующее значение. На большинстве устройств часы синхронизируются по сети автоматически, так что погрешность обычно составляет доли секунды. Секунды не теряются и в фоне: браузер продолжает выполнять таймеры в свёрнутой вкладке, а при возврате значение сразу прыгает на актуальное.</p>
<h3>Для чего нужен таймер обратного отсчёта</h3>
<ul>
<li>следить за дедлайнами по работе и учёбе;</li>
<li>считать время до отпуска, дня рождения или Нового года;</li>
<li>держать перед глазами старт распродажи или релиза;</li>
<li>засекать остаток времени на экзамене или тренировке.</li>
</ul>
<p>Главная польза такого таймера — наглядность: абстрактная дата в календаре превращается в живые цифры, которые тают на глазах. Это дисциплинирует лучше любой заметки в ежедневнике. Держите страницу открытой в отдельной вкладке — и важный срок всегда будет перед глазами, без напоминаний и будильников.</p>""",
  "faq": [
    ("Отсчёт идёт в моём часовом поясе или в UTC?",
     "В локальном поясе вашего устройства: поле ввода трактуется как локальное время. Если цель задана в другом поясе, переведите её в своё время заранее — например, нашим калькулятором часовых поясов."),
    ("Что показывает прогресс-бар?",
     "Долю времени, прошедшую с момента открытия страницы до цели. Обновите страницу — и бар начнётся с нуля, хотя сам остаток времени не изменится."),
    ("Почему при выборе прошедшей даты таймер не идёт?",
     "Отсчёт в прошлое бессмысленен: таймер сразу показывает «Время наступило!» и подсказку выбрать момент в будущем."),
    ("Таймер работает, если вкладка свернута?",
     "Да, браузер продолжает выполнять таймеры в фоне. При возврате во вкладку значение может прыгнуть сразу на актуальное — это нормально, секунды не теряются."),
    ("Как поставить отсчёт до Нового года?",
     "Ничего делать не нужно: ближайший Новый год стоит целью по умолчанию. Откройте страницу — и отсчёт уже идёт."),
    ("Почему мой таймер расходится с таймером коллеги?",
     "Скорее всего, у вас разные часовые пояса или на одном из устройств сбиты часы. Сверьте пояс и включите автоматическую синхронизацию времени в настройках системы."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var targetEl = document.getElementById('cd-target');
  var startBtn = document.getElementById('cd-start');
  var errEl = document.getElementById('cd-error');
  var valueEl = document.getElementById('cd-value');
  var targetOutEl = document.getElementById('cd-target-out');
  var pctEl = document.getElementById('cd-pct');
  var barEl = document.getElementById('cd-bar');

  // Прогресс-бар отсчитывается от момента загрузки страницы — по ТЗ.
  var pageStart = Date.now();
  var targetMs = null;

  function pad(n){ return n < 10 ? '0' + n : '' + n; }

  function setDefault(){
    var now = new Date();
    var ny = new Date(now.getFullYear() + 1, 0, 1, 0, 0, 0);
    targetEl.value = ny.getFullYear() + '-' + pad(ny.getMonth() + 1) + '-' + pad(ny.getDate()) +
                     'T' + pad(ny.getHours()) + ':' + pad(ny.getMinutes());
  }

  function readTarget(){
    var v = targetEl.value;
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/.exec(v || '');
    if (!m) return null;
    var ms = new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], m[6] ? +m[6] : 0).getTime();
    return isNaN(ms) ? null : ms;
  }

  function update(){
    if (targetMs === null) return;
    var now = Date.now();
    var diff = targetMs - now;
    if (diff <= 0){
      valueEl.textContent = 'Время наступило!';
      barEl.style.width = '100%';
      pctEl.textContent = '100%';
      return;
    }
    var sec = Math.floor(diff / 1000);
    var d = Math.floor(sec / 86400);
    var h = Math.floor((sec % 86400) / 3600);
    var mi = Math.floor((sec % 3600) / 60);
    var s = sec % 60;
    valueEl.textContent = d + ' : ' + pad(h) + ' : ' + pad(mi) + ' : ' + pad(s);
    var total = targetMs - pageStart;
    var pct = total > 0 ? (now - pageStart) / total * 100 : 100;
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    barEl.style.width = pct.toFixed(1) + '%';
    pctEl.textContent = Math.round(pct) + '%';
  }

  function restart(){
    var ms = readTarget();
    if (ms === null){
      errEl.textContent = 'Выберите дату и время цели.';
      errEl.classList.add('visible');
      valueEl.textContent = '—';
      targetMs = null;
      return;
    }
    if (ms <= Date.now()){
      errEl.textContent = 'Эта дата уже в прошлом — выберите момент в будущем.';
      errEl.classList.add('visible');
    } else {
      errEl.classList.remove('visible');
    }
    targetMs = ms;
    var d = new Date(ms);
    targetOutEl.textContent = pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + d.getFullYear() +
                            ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    update();
  }

  targetEl.addEventListener('change', restart);
  targetEl.addEventListener('input', restart);
  startBtn.addEventListener('click', restart);
  setDefault();
  restart();
  setInterval(update, 1000);
})();
""",
  "page_css": ".cd-digits{font-size:clamp(1.6rem,5vw,2.4rem);letter-spacing:.02em}.cd-labels{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font-size:.72rem;color:var(--ink-soft);font-family:var(--font-mono);text-transform:uppercase;letter-spacing:.05em;margin-top:-6px}.cd-labels span{text-align:left}.cd-bar{height:8px;background:var(--surface-2);border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-top:16px}.cd-bar-fill{height:100%;width:0;background:var(--accent);transition:width .6s ease}.cd-rows{margin-top:14px}@media(max-width:640px){input[type=\"datetime-local\"]{padding-right:40px;font-size:14px}}",
  "related": ["unix-vremya", "dni", "rabochie-dni", "chasovye-poyasa"],
}
