# -*- coding: utf-8 -*-
# Проверка номера банковской карты: Лун + платёжная система по IIN. Только локально.

TOOL = {
  "slug": "proverka-nomera-karty",
  "title": "Проверка номера карты",
  "meta_title": "Проверка номера банковской карты — алгоритм Луна",
  "meta_desc": "Проверьте номер карты по алгоритму Луна и определите платёжную систему: Мир, Visa, Mastercard, Amex, UnionPay, JCB. Номер никуда не отправляется.",
  "h1": "Проверка номера банковской карты",
  "sub": "Алгоритм Луна и определение платёжной системы — вычисления только в вашем браузере.",
  "category": "Проверка данных",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <label for="card-in">Номер карты</label>
    <input type="text" id="card-in" inputmode="numeric" maxlength="23" placeholder="0000 0000 0000 0000" autocomplete="off">
    <span class="hint">Пробелы и дефисы допустимы. Номер не отправляется на сервер и не сохраняется.</span>
    <div class="error-msg" id="card-error" role="alert">В номере карты от 13 до 19 цифр.</div>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Результат проверки</div>
  <div class="r-value" id="card-verdict">—</div>
  <div class="r-rows">
    <div><b id="card-brand">—</b><span>платёжная система</span></div>
    <div><b id="card-luhn">—</b><span>алгоритм Луна</span></div>
    <div><b id="card-mask">—</b><span>маскированный номер</span></div>
    <div><b id="card-len">—</b><span>цифр в номере</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Безопасность прежде всего: номер карты обрабатывается только в вашем браузере. Страница не отправляет его на сервер, не сохраняет и даже не показывает целиком в результатах — видны лишь четыре последние цифры. Проверять номера чужих карт здесь безопасно, но помните: корректный по Луну номер ещё не значит, что карта существует и активна.</p>
<p>Алгоритм Луна — контрольная сумма, встроенная в номер любой банковской карты. Цифры справа налево через одну удваиваются (если результат больше 9, из него вычитается 9), всё складывается, и итог должен делиться на 10. Это защита от опечаток, а не от мошенничества: случайно ошибиться в одной цифре не выйдет, а вот придумать проходящий проверку номер — элементарно.</p>
<p>Платёжная система определяется по первым цифрам (IIN/BIN): 4 — Visa, 5 — Mastercard, 34 и 37 — American Express, 62 — UnionPay, 35 — JCB, 2 — Мир, включая диапазон 2200–2204. Правила упрощены: реальные таблицы BIN содержат тысячи диапазонов и периодически меняются, поэтому для спорных случаев сверяйтесь с банком-эмитентом.</p>""",
  "faq": [
    ("Безопасно ли вводить номер карты на этой странице?",
     "Да: все вычисления выполняются локально в браузере, сетевых запросов с номером нет. Для полной уверенности можно даже отключить интернет после загрузки страницы — проверка продолжит работать."),
    ("Номер прошёл проверку Луна — значит, карта настоящая?",
     "Не обязательно. Алгоритм Луна ловит опечатки, но подобрать математически корректный номер несложно. Реальность карты подтверждает только банк-эмитент."),
    ("Почему не определилась платёжная система?",
     "Мы определяем систему по упрощённым правилам по первым цифрам. Новые и редкие диапазоны BIN (например, виртуальные карты некоторых банков) могут не попасть в список."),
    ("Сколько цифр должно быть в номере?",
     "Обычно 16, у карт Мир — от 16 до 19, у American Express — 15. Стандарт допускает от 13 до 19 цифр."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var inEl = document.getElementById('card-in');
  var errEl = document.getElementById('card-error');
  var verdictEl = document.getElementById('card-verdict');
  var brandEl = document.getElementById('card-brand');
  var luhnEl = document.getElementById('card-luhn');
  var maskEl = document.getElementById('card-mask');
  var lenEl = document.getElementById('card-len');

  function luhnOk(digits){
    var sum = 0;
    var dbl = false;
    for (var i = digits.length - 1; i >= 0; i--){
      var d = digits.charCodeAt(i) - 48;
      if (dbl){
        d *= 2;
        if (d > 9) d -= 9;
      }
      sum += d;
      dbl = !dbl;
    }
    return sum % 10 === 0;
  }

  function detectBrand(d){
    var p4 = parseInt(d.slice(0, 4), 10);
    if (p4 >= 2200 && p4 <= 2204) return 'Мир';
    if (d.charAt(0) === '2') return 'Мир';
    if (d.charAt(0) === '4') return 'Visa';
    if (d.charAt(0) === '5') return 'Mastercard';
    if (/^3[47]/.test(d)) return 'American Express';
    if (/^62/.test(d)) return 'UnionPay';
    if (/^35/.test(d)) return 'JCB';
    return 'не определена';
  }

  function showError(msg){
    errEl.textContent = msg;
    errEl.classList.add('visible');
  }
  function hideError(){ errEl.classList.remove('visible'); }

  function reset(){
    verdictEl.textContent = '—';
    verdictEl.style.color = '';
    brandEl.textContent = '—';
    luhnEl.textContent = '—';
    maskEl.textContent = '—';
    lenEl.textContent = '—';
  }

  function render(){
    if (inEl.value.trim() === ''){ hideError(); reset(); return; }
    var raw = inEl.value.replace(/[\s-]/g, '');
    if (!/^\d+$/.test(raw)){
      showError('Номер карты состоит только из цифр.');
      reset();
      return;
    }
    if (raw.length < 13 || raw.length > 19){
      showError('В номере карты от 13 до 19 цифр. Сейчас введено: ' + raw.length + '.');
      reset();
      return;
    }
    hideError();

    var ok = luhnOk(raw);
    verdictEl.textContent = ok ? 'Номер корректный' : 'Номер некорректный';
    verdictEl.style.color = ok ? 'var(--accent)' : 'var(--danger)';
    brandEl.textContent = detectBrand(raw);
    luhnEl.textContent = ok ? 'пройден' : 'не пройден';
    lenEl.textContent = String(raw.length);
    maskEl.textContent = '•••• ' + raw.slice(-4);
  }

  inEl.addEventListener('input', render);
  render();
})();
""",
  "page_css": "",
  "related": ["proverka-inn", "proverka-snils", "generator-paroley", "uuid-generator"],
}
