# -*- coding: utf-8 -*-
# Проверка СНИЛС (11 цифр, контрольное число mod 101).

TOOL = {
  "slug": "proverka-snils",
  "title": "Проверка СНИЛС",
  "meta_title": "Проверка СНИЛС онлайн — контрольная сумма",
  "meta_desc": "Проверьте номер СНИЛС по контрольной сумме: первые 9 цифр с весами от 9 до 1, остаток по модулю 101. Локально, без отправки данных.",
  "h1": "Проверка СНИЛС",
  "sub": "Проверка контрольного числа страхового номера — мгновенно и локально в браузере.",
  "category": "Проверка данных",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <label for="snils-in">СНИЛС</label>
    <input type="text" id="snils-in" inputmode="numeric" maxlength="14" placeholder="123-456-789 01" data-share="snils">
    <span class="hint">Можно вводить с пробелами и дефисами — лишнее отбросится.</span>
    <div class="error-msg" id="snils-error" role="alert">СНИЛС состоит из 11 цифр.</div>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Результат проверки</div>
  <div class="r-value" id="snils-verdict">—</div>
  <div class="r-rows">
    <div><b id="snils-expected">—</b><span>ожидаемое контрольное число</span></div>
    <div><b id="snils-actual">—</b><span>фактическое (две последние цифры)</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Две последние цифры СНИЛС — контрольное число, которое вычисляется из первых девяти. Каждая из девяти цифр умножается на вес, равный её позиции с конца: первая — на 9, вторая — на 8 и так до девятой с весом 1. Сумма произведений берётся по модулю 101: остаток от 0 до 99 и есть контрольное число, а остаток 100 превращается в 00.</p>
<p>Номер 000-000-000 00 формально прошёл бы эту проверку, но такие СНИЛС не выдаются, поэтому сервис считает его недействительным.</p>
<p>Как и с ИНН, успешная проверка подтверждает лишь математическую корректность номера, а не его существование в базе Пенсионного фонда (ныне Социального фонда России). Вычисления выполняются локально: номер не покидает ваш браузер.</p>""",
  "faq": [
    ("Что означает «контрольное число не сошлось»?",
     "Сумма первых девяти цифр с весами, взятая по модулю 101, не равна двум последним цифрам. Почти всегда это опечатка — перепроверьте номер по зелёной карточке."),
    ("Можно ли проверить СНИЛС ребёнка?",
     "Да, алгоритм одинаков для всех номеров независимо от возраста владельца."),
    ("Почему контрольное число иногда 00?",
     "Когда сумма с весами делится на 101 без остатка или даёт остаток 100, контрольное число записывается как 00. Это штатная ситуация, а не ошибка."),
    ("Номер отправляется на сервер?",
     "Нет. Проверка выполняется только в вашем браузере, сетевых запросов нет."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var inEl = document.getElementById('snils-in');
  var errEl = document.getElementById('snils-error');
  var verdictEl = document.getElementById('snils-verdict');
  var expectedEl = document.getElementById('snils-expected');
  var actualEl = document.getElementById('snils-actual');

  function showError(msg){
    errEl.textContent = msg;
    errEl.classList.add('visible');
  }
  function hideError(){ errEl.classList.remove('visible'); }

  function pad2(n){ return n < 10 ? '0' + n : '' + n; }

  function reset(){
    verdictEl.textContent = '—';
    verdictEl.style.color = '';
    expectedEl.textContent = '—';
    actualEl.textContent = '—';
  }

  function render(){
    if (inEl.value.trim() === ''){ hideError(); reset(); return; }
    var raw = inEl.value.replace(/\D/g, '');
    if (raw.length !== 11){
      showError('СНИЛС состоит из 11 цифр. Сейчас введено: ' + raw.length + '.');
      reset();
      return;
    }
    hideError();

    var digits = [];
    for (var i = 0; i < 11; i++) digits.push(raw.charCodeAt(i) - 48);

    var sum = 0;
    var allZero = true;
    for (var k = 0; k < 9; k++){
      sum += digits[k] * (9 - k);
      if (digits[k] !== 0) allZero = false;
    }
    var expected = sum % 101;
    if (expected === 100) expected = 0;
    var actual = digits[9] * 10 + digits[10];
    var ok = !allZero && expected === actual;

    verdictEl.textContent = ok ? 'СНИЛС действительный' : 'СНИЛС недействительный';
    verdictEl.style.color = ok ? 'var(--accent)' : 'var(--danger)';
    expectedEl.textContent = pad2(expected);
    actualEl.textContent = pad2(actual);
  }

  inEl.addEventListener('input', render);
  render();
})();
""",
  "page_css": "",
  "related": ["proverka-inn", "trudovoy-stazh", "strahovye-vznosy-ip", "dekretnye"],
}
