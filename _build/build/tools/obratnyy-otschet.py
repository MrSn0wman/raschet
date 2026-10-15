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
    <input type="datetime-local" id="cd-target" step="1">
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
  "explain_html": """<h2>Как это работает</h2>
<p>Таймер раз в секунду сравнивает текущее время устройства с целевым моментом и показывает остаток в днях, часах, минутах и секундах. По умолчанию целью стоит ближайший Новый год — поле можно поменять на любую дату и время, отсчёт перезапустится автоматически.</p>
<p>Прогресс-бар показывает, какая доля времени прошла с момента открытия страницы до цели: при загрузке он всегда на нуле и растёт по мере приближения к целевой дате. Это честная метрика «сколько уже выждали» за текущий сеанс, а не доля от начала времён.</p>
<p>Учтите: отсчёт опирается на часы вашего устройства и его часовой пояс. Если часы компьютера сбиты, таймер покажет соответствующее значение. Когда цель наступает, таймер останавливается на сообщении «Время наступило!» — отрицательных значений не бывает.</p>""",
  "faq": [
    ("Отсчёт идёт в моём часовом поясе или в UTC?",
     "В локальном поясе вашего устройства: поле ввода трактуется как локальное время. Если цель задана в другом поясе, переведите её в своё время заранее — например, нашим калькулятором часовых поясов."),
    ("Что показывает прогресс-бар?",
     "Долю времени, прошедшую с момента открытия страницы до цели. Обновите страницу — и бар начнётся с нуля, хотя сам остаток времени не изменится."),
    ("Почему при выборе прошедшей даты таймер не идёт?",
     "Отсчёт в прошлое бессмысленен: таймер сразу показывает «Время наступило!» и подсказку выбрать момент в будущем."),
    ("Таймер работает, если вкладка свернута?",
     "Да, браузер продолжает выполнять таймеры в фоне. При возврате во вкладку значение может прыгнуть сразу на актуальное — это нормально, секунды не теряются."),
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
  "page_css": ".cd-digits{font-size:clamp(1.6rem,5vw,2.4rem);letter-spacing:.02em}.cd-labels{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font-size:.72rem;color:var(--ink-soft);font-family:var(--font-mono);text-transform:uppercase;letter-spacing:.05em;margin-top:-6px}.cd-labels span{text-align:left}.cd-bar{height:8px;background:var(--surface-2);border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-top:16px}.cd-bar-fill{height:100%;width:0;background:var(--accent);transition:width .6s ease}.cd-rows{margin-top:14px}",
  "related": ["unix-vremya", "dni", "rabochie-dni", "chasovye-poyasa"],
}
