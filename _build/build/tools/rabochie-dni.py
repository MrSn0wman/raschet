# -*- coding: utf-8 -*-
# Калькулятор рабочих дней: между датами / прибавить N рабочих дней.

TOOL = {
  "slug": "rabochie-dni",
  "title": "Калькулятор рабочих дней",
  "meta_title": "Калькулятор рабочих дней — выходные и праздники РФ",
  "meta_desc": "Посчитайте рабочие дни между датами или прибавьте N рабочих дней к дате. Учёт суббот, воскресений и фиксированных праздников РФ.",
  "h1": "Калькулятор рабочих дней",
  "sub": "Сколько рабочих дней в периоде или какая дата наступит через N рабочих дней.",
  "category": "Дата и время",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <div class="strategy-toggle">
      <label class="strategy-option"><input type="radio" name="wd-mode" value="between" checked><span><b>Между двумя датами</b><small>Сколько рабочих дней в периоде, включая обе даты</small></span></label>
      <label class="strategy-option"><input type="radio" name="wd-mode" value="add"><span><b>Прибавить рабочие дни</b><small>Какая дата наступит через N рабочих дней</small></span></label>
    </div>
  </div>
  <div class="field">
    <label for="wd-from">Начальная дата</label>
    <input type="date" id="wd-from">
  </div>
  <div class="field" id="wd-to-wrap">
    <label for="wd-to">Конечная дата</label>
    <input type="date" id="wd-to">
  </div>
  <div class="field" id="wd-n-wrap" style="display:none">
    <label for="wd-n">Прибавить рабочих дней</label>
    <input type="number" id="wd-n" min="0" max="3650" value="10" step="1">
  </div>
  <div class="field full">
    <label class="check-option"><input type="checkbox" id="wd-holidays"> Учитывать праздники РФ</label>
    <div class="error-msg" id="wd-error" role="alert">Проверьте даты и число дней.</div>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label" id="wd-label">Рабочих дней в периоде</div>
  <div class="r-value" id="wd-result">—</div>
  <div class="r-rows">
    <div><b id="wd-total">—</b><span>календарных дней</span></div>
    <div><b id="wd-weekends">—</b><span>суббот и воскресений</span></div>
    <div><b id="wd-hols">—</b><span>праздничных будней</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>В режиме «между датами» калькулятор перебирает все дни периода включительно (обе крайние даты считаются) и отбрасывает субботы и воскресенья. В режиме «прибавить N дней» стартовая дата сама не считается: отсчёт начинается со следующего дня, и ищется дата, на которую придётся N-й рабочий день. При N = 0 результат — сама стартовая дата.</p>
<p>Галочка «учитывать праздники РФ» дополнительно вычитает будни, попадающие на фиксированные праздничные даты: 1–8 января, 23 февраля, 8 марта, 1 и 9 мая, 12 июня и 4 ноября.</p>
<p><b>Честная оговорка.</b> Мы не моделируем переносы выходных: когда праздник выпадает на субботу или воскресенье, правительство переносит выходной на ближайший будний день, и эти переносы каждый год утверждаются отдельным постановлением. Наш список — только фиксированные даты. Для точных расчётов сроков по договорам сверяйтесь с официальным производственным календарём на нужный год.</p>""",
  "faq": [
    ("Крайние даты входят в подсчёт?",
     "Да, в режиме «между датами» начальная и конечная даты считаются, если это рабочие дни. В режиме «прибавить» стартовая дата не считается — отсчёт идёт со следующего дня."),
    ("Почему результат с праздниками может не совпасть с производственным календарём?",
     "Мы учитываем только фиксированные праздничные даты без переносов выходных, которые каждый год утверждаются постановлением. Из-за переносов реальное число рабочих дней может отличаться на несколько дней."),
    ("Как посчитать дедлайн «10 рабочих дней с даты договора»?",
     "Выберите режим «Прибавить рабочие дни», укажите дату договора и число 10. Если формулировка «в течение 10 рабочих дней со дня…», отсчёт обычно начинается со следующего дня — именно так считает калькулятор."),
    ("Можно ли посчитать период в несколько лет?",
     "Да, до 100 лет в режиме «между датами» и до 3650 рабочих дней в режиме «прибавить». Это покрывает любые реальные задачи, включая долгосрочные договоры."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  // Фиксированные праздничные даты РФ (месяц-день). Переносы выходных не моделируются.
  var HOLIDAYS = {
    '01-01': 1, '01-02': 1, '01-03': 1, '01-04': 1, '01-05': 1, '01-06': 1, '01-07': 1, '01-08': 1,
    '02-23': 1, '03-08': 1, '05-01': 1, '05-09': 1, '06-12': 1, '11-04': 1
  };

  var fromEl = document.getElementById('wd-from');
  var toEl = document.getElementById('wd-to');
  var nEl = document.getElementById('wd-n');
  var toWrap = document.getElementById('wd-to-wrap');
  var nWrap = document.getElementById('wd-n-wrap');
  var holEl = document.getElementById('wd-holidays');
  var errEl = document.getElementById('wd-error');
  var labelEl = document.getElementById('wd-label');
  var resultEl = document.getElementById('wd-result');
  var totalEl = document.getElementById('wd-total');
  var weekendsEl = document.getElementById('wd-weekends');
  var holsEl = document.getElementById('wd-hols');

  function pad(n){ return n < 10 ? '0' + n : '' + n; }

  function plural(n, one, few, many){
    var m = Math.abs(n) % 100;
    var d = m % 10;
    if (m > 10 && m < 20) return many;
    if (d > 1 && d < 5) return few;
    if (d === 1) return one;
    return many;
  }

  function parseDate(v){
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || '');
    if (!m) return null;
    var d = new Date(+m[1], +m[2] - 1, +m[3]);
    return isNaN(d.getTime()) ? null : d;
  }

  function fmt(d){
    return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + d.getFullYear();
  }

  function dateKey(d){
    return pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }

  // Разбирает один день: возвращает 'weekend' | 'holiday' | 'work'.
  function dayKind(d, useHolidays){
    var day = d.getDay();
    if (day === 0 || day === 6) return 'weekend';
    if (useHolidays && HOLIDAYS[dateKey(d)]) return 'holiday';
    return 'work';
  }

  function showError(msg){
    errEl.textContent = msg;
    errEl.classList.add('visible');
  }
  function hideError(){ errEl.classList.remove('visible'); }

  function reset(){
    resultEl.textContent = '—';
    totalEl.textContent = '—';
    weekendsEl.textContent = '—';
    holsEl.textContent = '—';
  }

  function currentMode(){
    var checked = document.querySelector('input[name="wd-mode"]:checked');
    return checked ? checked.value : 'between';
  }

  function render(){
    var mode = currentMode();
    toWrap.style.display = mode === 'between' ? '' : 'none';
    nWrap.style.display = mode === 'add' ? '' : 'none';
    var useHolidays = holEl.checked;
    var from = parseDate(fromEl.value);

    if (mode === 'between'){
      labelEl.textContent = 'Рабочих дней в периоде';
      var to = parseDate(toEl.value);
      if (!from || !to){ reset(); return; }
      var start = from <= to ? from : to;
      var end = from <= to ? to : from;
      var days = Math.round((end - start) / 86400000) + 1;
      if (days > 36600){
        showError('Слишком длинный период — больше 100 лет.');
        reset();
        return;
      }
      hideError();
      var work = 0, weekends = 0, hols = 0;
      var cur = new Date(start.getTime());
      while (cur <= end){
        var kind = dayKind(cur, useHolidays);
        if (kind === 'work') work++;
        else if (kind === 'weekend') weekends++;
        else hols++;
        cur.setDate(cur.getDate() + 1);
      }
      resultEl.textContent = window.formatMoney(work) + ' ' + plural(work, 'рабочий день', 'рабочих дня', 'рабочих дней');
      totalEl.textContent = window.formatMoney(days);
      weekendsEl.textContent = window.formatMoney(weekends);
      holsEl.textContent = useHolidays ? window.formatMoney(hols) : 'не учитывались';
    } else {
      labelEl.textContent = 'Дата через N рабочих дней';
      var n = parseInt(nEl.value, 10);
      if (!from){ reset(); return; }
      if (isNaN(n) || n < 0 || n > 3650){
        showError('Укажите от 0 до 3650 рабочих дней.');
        reset();
        return;
      }
      hideError();
      var cur2 = new Date(from.getTime());
      var added = 0, skippedW = 0, skippedH = 0;
      var guard = 0;
      while (added < n && guard < 20000){
        cur2.setDate(cur2.getDate() + 1);
        guard++;
        var kind2 = dayKind(cur2, useHolidays);
        if (kind2 === 'work') added++;
        else if (kind2 === 'weekend') skippedW++;
        else skippedH++;
      }
      resultEl.textContent = fmt(cur2);
      totalEl.textContent = window.formatMoney(Math.round((cur2 - from) / 86400000));
      weekendsEl.textContent = window.formatMoney(skippedW);
      holsEl.textContent = useHolidays ? window.formatMoney(skippedH) : 'не учитывались';
    }
  }

  function initDates(){
    var now = new Date();
    var later = new Date(now.getTime());
    later.setDate(later.getDate() + 14);
    if (!fromEl.value) fromEl.value = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate());
    if (!toEl.value) toEl.value = later.getFullYear() + '-' + pad(later.getMonth() + 1) + '-' + pad(later.getDate());
  }

  document.querySelectorAll('input[name="wd-mode"]').forEach(function(r){
    r.addEventListener('change', render);
  });
  [fromEl, toEl, nEl].forEach(function(el){
    el.addEventListener('input', render);
    el.addEventListener('change', render);
  });
  holEl.addEventListener('change', render);
  initDates();
  render();
})();
""",
  "page_css": "",
  "related": ["dni", "otpusknye-dni", "trudovoy-stazh", "obratnyy-otschet"],
}
