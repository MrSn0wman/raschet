# -*- coding: utf-8 -*-
# Конвертер валют: курсы ЦБ РФ через API с офлайн-фолбэком.

TOOL = {
  "slug": "konverter-valyut",
  "title": "Конвертер валют",
  "meta_title": "Конвертер валют онлайн — курс ЦБ, USD, EUR, CNY",
  "meta_desc": "Переведите рубли в доллары, евро, юани и ещё 7 валют по курсу ЦБ РФ. Работает и без интернета — на офлайн-курсах с указанием даты.",
  "h1": "Конвертер валют",
  "sub": "Перевод суммы между рублём и девятью валютами по курсу ЦБ РФ.",
  "category": "Конвертеры",
  "fields_html": """
<div class="field-grid">
  <div class="field">
    <label for="cv-amount">Сумма</label>
    <div class="unit-input"><input type="text" id="cv-amount" value="1000" inputmode="numeric" data-share="amount"><span id="cv-unit">USD</span></div>
  </div>
  <div class="field">
    <label for="cv-from">Из валюты</label>
    <select id="cv-from" data-share="from">
      <option value="USD" selected>USD — доллар США</option>
      <option value="EUR">EUR — евро</option>
      <option value="CNY">CNY — китайский юань</option>
      <option value="GBP">GBP — фунт стерлингов</option>
      <option value="TRY">TRY — турецкая лира</option>
      <option value="AED">AED — дирхам ОАЭ</option>
      <option value="KZT">KZT — казахский тенге</option>
      <option value="BYN">BYN — белорусский рубль</option>
      <option value="UAH">UAH — украинская гривна</option>
      <option value="RUB">RUB — российский рубль</option>
    </select>
  </div>
  <div class="field">
    <label for="cv-to">В валюту</label>
    <select id="cv-to" data-share="to">
      <option value="RUB" selected>RUB — российский рубль</option>
      <option value="USD">USD — доллар США</option>
      <option value="EUR">EUR — евро</option>
      <option value="CNY">CNY — китайский юань</option>
      <option value="GBP">GBP — фунт стерлингов</option>
      <option value="TRY">TRY — турецкая лира</option>
      <option value="AED">AED — дирхам ОАЭ</option>
      <option value="KZT">KZT — казахский тенге</option>
      <option value="BYN">BYN — белорусский рубль</option>
      <option value="UAH">UAH — украинская гривна</option>
    </select>
  </div>
  <div class="field full">
    <span class="hint" id="cv-src">Курсы ЦБ РФ от 15.10.2026 (офлайн)</span>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Итог конвертации</div>
  <div class="r-value" id="cv-result">—</div>
  <div class="r-rows">
    <div><b id="cv-rate">—</b><span>прямой курс</span></div>
    <div><b id="cv-inv">—</b><span>обратный курс</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Калькулятор берёт курсы Центрального банка РФ: сначала пытается получить свежие данные с нашего сервера (запрос ждёт ответ не дольше трёх секунд), а если сервер недоступен — считает по офлайн-курсам, зашитым в страницу. В офлайн-режиме рядом с результатом всегда указана дата, на которую курсы актуальны. Если сервер вернул устаревшие данные, вы увидите пометку «обновление временно недоступно» — расчёт при этом остаётся корректным на указанную дату.</p>
<p>Все курсы приведены к одной единице валюты. У ЦБ гривна публикуется «за 10», а тенге — «за 100»; мы пересчитываем номиналы, поэтому сравнивать валюты можно напрямую. Конвертация между любыми парами (например, EUR → CNY) идёт через рубль: сумма сначала переводится в рубли по курсу исходной валюты, затем из рублей — в целевую валюту. Это тот же принцип кросс-курсов, которым пользуются банки.</p>
<p>Важно: курс ЦБ — официальный ориентир, а не цена сделки. Банки и обменники добавляют к нему свою маржу, поэтому реальный курс покупки или продажи валюты будет отличаться обычно на 1–3%.</p>""",
  "faq": [
    ("Почему в банке курс отличается от показанного здесь?",
     "Здесь — официальный курс ЦБ РФ. Банки продают и покупают валюту с наценкой: курс покупки ниже курса ЦБ, курс продажи выше. Разница обычно составляет 1–3%."),
    ("Что означает пометка «офлайн»?",
     "Сервер с актуальными курсами не ответил за три секунды, и расчёт выполнен по курсам, сохранённым прямо в странице. Дата этих курсов указана в пометке."),
    ("Как перевести евро в доллары, если курс задан только к рублю?",
     "Ничего дополнительно делать не нужно: выберите «из валюты» EUR, «в валюту» USD. Конвертер сам пересчитает сумму через рубль по кросс-курсу."),
    ("Как часто обновляются курсы?",
     "ЦБ РФ публикует официальные курсы один раз в рабочий день, около 13:30 мск; на выходные и праздники действует курс пятницы. Наш сервер забирает обновление сразу после публикации."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  // Офлайн-курсы ЦБ РФ, рублей за 1 единицу валюты (номиналы уже приведены).
  var OFFLINE_DATE = '15.10.2026';
  var OFFLINE = {
    USD: 83.9497, EUR: 93.9229, CNY: 12.5358, GBP: 111.225, TRY: 1.702,
    AED: 22.859, KZT: 0.1872, BYN: 27.8782, UAH: 1.8664, RUB: 1
  };

  var rates = {};
  Object.keys(OFFLINE).forEach(function(code){ rates[code] = OFFLINE[code]; });

  var amountEl = document.getElementById('cv-amount');
  var fromEl = document.getElementById('cv-from');
  var toEl = document.getElementById('cv-to');
  var unitEl = document.getElementById('cv-unit');
  var outEl = document.getElementById('cv-result');
  var rateEl = document.getElementById('cv-rate');
  var invEl = document.getElementById('cv-inv');
  var srcEl = document.getElementById('cv-src');

  function render(){
    var amount = window.parseFormattedNumber(amountEl);
    var from = fromEl.value;
    var to = toEl.value;
    unitEl.textContent = from;
    if (isNaN(amount) || !rates[from] || !rates[to]){
      outEl.textContent = '—';
      rateEl.textContent = '—';
      invEl.textContent = '—';
      return;
    }
    var result = amount * rates[from] / rates[to];
    outEl.textContent = window.formatMoney2(result) + ' ' + to;
    rateEl.textContent = '1 ' + from + ' = ' + window.formatSmart(rates[from] / rates[to]) + ' ' + to;
    invEl.textContent = '1 ' + to + ' = ' + window.formatSmart(rates[to] / rates[from]) + ' ' + from;
  }

  function loadRates(){
    if (!window.RASCHET_API_BASE){
      srcEl.textContent = 'Курсы ЦБ РФ от ' + OFFLINE_DATE + ' (офлайн)';
      return;
    }
    var ctrl = new AbortController();
    var timer = setTimeout(function(){ ctrl.abort(); }, 3000);
    fetch(window.RASCHET_API_BASE + '/api/rates', { signal: ctrl.signal })
      .then(function(resp){
        if (!resp.ok) throw new Error('http ' + resp.status);
        return resp.json();
      })
      .then(function(data){
        clearTimeout(timer);
        if (!data || typeof data !== 'object' || !data.rates) throw new Error('format');
        Object.keys(rates).forEach(function(code){
          if (code === 'RUB') return;
          var v = Number(data.rates[code]);
          if (isFinite(v) && v > 0) rates[code] = v;
        });
        if (data.stale){
          srcEl.textContent = 'Курсы от ' + String(data.date || OFFLINE_DATE) + ', обновление временно недоступно';
        } else {
          srcEl.textContent = 'Курсы ЦБ РФ от ' + String(data.date || OFFLINE_DATE);
        }
        render();
      })
      .catch(function(){
        clearTimeout(timer);
        srcEl.textContent = 'Курсы ЦБ РФ от ' + OFFLINE_DATE + ' (офлайн)';
      });
  }

  window.attachThousandsInput(amountEl);
  amountEl.addEventListener('input', render);
  fromEl.addEventListener('change', render);
  toEl.addEventListener('change', render);
  render();
  loadRates();
})();
""",
  "page_css": "",
  "related": ["procenty", "slozhnyy-procent", "skidki", "chasovye-poyasa"],
}
