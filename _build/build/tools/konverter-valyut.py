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
  "explain_html": """<h2>Как считается конвертация валют</h2>
<p>Конвертер переводит суммы между рублём и девятью иностранными валютами по официальным курсам Центрального банка РФ. Введите сумму, выберите валюту «из» и валюту «в» — итог, прямой и обратный курс появятся сразу. Под курсом указана дата, на которую он действует, а расчёт пересчитывается при каждом изменении полей.</p>
<p>ЦБ публикует курсы всех валют в рублях, поэтому любая пара считается через рубль. Сумма сначала переводится в рубли по курсу исходной валюты, затем из рублей — в целевую:</p>
<p><code>результат = сумма × курс исходной / курс целевой</code></p>
<p>Пример по курсам, зашитым в страницу на 15.10.2026: доллар — 83,9497&nbsp;₽, евро — 93,9229&nbsp;₽. Переведём 100 долларов в евро: 100 × 83,9497 / 93,9229 ≈ 89,38 €. Это и есть кросс-курс — тот же принцип банки используют, обменивая одну иностранную валюту на другую без рублей в кассе.</p>
<p>Под результатом видны два справочных значения. Прямой курс — сколько целевой валюты дают за одну единицу исходной; обратный — наоборот. По ним удобно проверить расчёт или прикинуть сделку в другую сторону, не меняя поля местами.</p>
<p>Кроме рубля доступны доллар США, евро, китайский юань, британский фунт, турецкая лира, дирхам ОАЭ, казахстанский тенге, белорусский рубль и украинская гривна. Пары собираются в любую сторону — хоть юани в тенге, хоть фунты в дирхамы: расчёт всё равно пройдёт через рубль по курсам ЦБ.</p>
<p>Официальный курс нужен не только туристам: по нему пересчитывают таможенные платежи, валютную выручку в отчётности и цены в контрактах с иностранными партнёрами. Для таких задач важна и дата курса — она всегда указана под результатом.</p>
<p>Если нужной валюты нет в списке, пересчитайте её в два шага: сначала переведите сумму в доллары или евро по курсу вашего банка, а затем — из них в рубли здесь. Копейки в итоге сохраняются: результат округляется до двух знаков, как принято в денежных расчётах.</p>
<h3>Курс ЦБ и курс в банке — не одно и то же</h3>
<p>Курс ЦБ — официальный ориентир для бухгалтерии, таможни и контрактов, а не цена сделки в кассе. Банки и обменники закладывают маржу: продают валюту дороже курса ЦБ, покупают дешевле, и разница обычно составляет 1–3%. При официальном курсе около 84&nbsp;₽ за доллар банк может продавать по 85–86&nbsp;₽, а покупать по 82–83&nbsp;₽: на сумме в 1&nbsp;000 $ разница с расчётом по ЦБ выльется в пару тысяч рублей. Поэтому конвертер отвечает на вопрос «сколько это по официальному курсу», а реальный курс обмена уточняйте в своём банке.</p>
<h3>Номиналы: за сколько единиц дан курс</h3>
<p>Некоторые курсы ЦБ публикует не за одну единицу валюты: гривна — за 10, тенге — за 100. Если смотреть на них без поправки, тенге кажется в разы дороже, чем есть на самом деле. Конвертер сам делит на номинал и показывает цену ровно одной единицы, поэтому валюты сравниваются напрямую и сюрпризов в расчёте нет.</p>
<h3>Откуда берутся курсы и зачем нужен офлайн-режим</h3>
<p>При открытии страница запрашивает свежие курсы у сервера и ждёт ответ не дольше трёх секунд. Успех — считаем по актуальным данным, дата указана под курсом. Нет ответа — включается офлайн-режим: расчёт идёт по курсам, сохранённым в самой странице, с пометкой «офлайн» и датой этих курсов. Бывает и третий вариант: сервер ответил, но свежих данных у него нет, — тогда появляется пометка «обновление временно недоступно», а расчёт остаётся корректным на указанную дату. Курсы ЦБ обновляются раз в рабочий день, в первой половине дня; на выходные и праздники действует курс пятницы.</p>""",
  "faq": [
    ("Почему в банке курс отличается от показанного здесь?",
     "Здесь — официальный курс ЦБ РФ. Банки продают и покупают валюту с наценкой: курс покупки ниже курса ЦБ, курс продажи выше. Разница обычно составляет 1–3%."),
    ("Что означает пометка «офлайн»?",
     "Сервер с актуальными курсами не ответил за три секунды, и расчёт выполнен по курсам, сохранённым прямо в странице. Дата этих курсов указана в пометке."),
    ("Как перевести евро в доллары, если курс задан только к рублю?",
     "Ничего дополнительно делать не нужно: выберите «из валюты» EUR, «в валюту» USD. Конвертер сам пересчитает сумму через рубль по кросс-курсу."),
    ("Как часто обновляются курсы?",
     "ЦБ РФ публикует официальные курсы один раз в рабочий день, в первой половине дня; на выходные и праздники действует курс пятницы. Наш сервер забирает обновление сразу после публикации."),
    ("Что показывают прямой и обратный курс под результатом?",
     "Прямой — сколько целевой валюты дают за одну единицу исходной, обратный — наоборот. По ним можно проверить расчёт без повторного ввода."),
    ("Почему курс тенге или гривны выглядит таким маленьким?",
     "ЦБ публикует эти курсы за 10 или 100 единиц, а конвертер показывает цену одной единицы. Поэтому тенге стоит копейки, а не рубли — так и должно быть."),
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

  function fmtRateDate(d){
    d = String(d || OFFLINE_DATE);
    return /^\d{4}-\d{2}-\d{2}$/.test(d) ? d.split('-').reverse().join('.') : d;
  }

  function offlineLabel(){
    srcEl.textContent = 'Курсы ЦБ РФ от ' + OFFLINE_DATE + ' (офлайн)';
  }

  function fetchRatesJson(url){
    var ctrl = new AbortController();
    var timer = setTimeout(function(){ ctrl.abort(); }, 3000);
    return fetch(url, { signal: ctrl.signal })
      .then(function(resp){
        clearTimeout(timer);
        if (!resp.ok) throw new Error('http ' + resp.status);
        return resp.json();
      }, function(err){ clearTimeout(timer); throw err; });
  }

  function applyRates(data){
    if (!data || typeof data !== 'object' || !data.rates) throw new Error('format');
    Object.keys(rates).forEach(function(code){
      if (code === 'RUB') return;
      var v = Number(data.rates[code]);
      if (isFinite(v) && v > 0) rates[code] = v;
    });
    var days = (Date.now() - Date.parse(fmtRateDate(data.date).split('.').reverse().join('-'))) / 86400000;
    if (data.stale || days > 14){
      srcEl.textContent = 'Курсы от ' + fmtRateDate(data.date) + ', обновление временно недоступно';
    } else {
      srcEl.textContent = 'Курсы ЦБ РФ от ' + fmtRateDate(data.date);
    }
    render();
  }

  function loadRates(){
    // 1) rates.json: ежедневные курсы ЦБ через GitHub Actions, same-origin.
    //    ?d=YYYYMMDD — дневной cache-bust, чтобы service worker не отдавал вчерашний файл.
    var t = new Date();
    var bust = '?d=' + t.getFullYear() + ('0' + (t.getMonth() + 1)).slice(-2) + ('0' + t.getDate()).slice(-2);
    fetchRatesJson('../assets/rates.json' + bust)
      .then(applyRates)
      .catch(function(){
        // 2) бэкенд (если настроен RASCHET_API_BASE)
        if (!window.RASCHET_API_BASE){ offlineLabel(); return; }
        fetchRatesJson(window.RASCHET_API_BASE + '/api/rates')
          .then(applyRates)
          .catch(offlineLabel);
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
