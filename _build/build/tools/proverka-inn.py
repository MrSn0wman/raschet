# -*- coding: utf-8 -*-
# Проверка ИНН (10 и 12 цифр) по контрольным суммам.

TOOL = {
  "slug": "proverka-inn",
  "title": "Проверка ИНН",
  "meta_title": "Проверка ИНН онлайн — контрольная сумма 10 и 12 цифр",
  "meta_desc": "Проверьте ИНН организации (10 цифр) или физлица и ИП (12 цифр) по контрольным суммам ФНС. Мгновенно, без отправки данных на сервер.",
  "h1": "Проверка ИНН",
  "sub": "Проверка контрольных цифр ИНН организации, физлица или ИП — мгновенно и локально.",
  "category": "Проверка данных",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <label for="inn-in">ИНН</label>
    <input type="text" id="inn-in" inputmode="numeric" maxlength="14" placeholder="10 или 12 цифр" data-share="inn">
    <span class="hint">10 цифр — организация, 12 цифр — физическое лицо или ИП.</span>
    <div class="error-msg" id="inn-error" role="alert">ИНН состоит из 10 или 12 цифр.</div>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Результат проверки</div>
  <div class="r-value" id="inn-verdict">—</div>
  <div class="r-rows">
    <div><b id="inn-type">—</b><span>тип ИНН</span></div>
    <div><b id="inn-check">—</b><span>контрольные цифры</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Последние одна или две цифры ИНН — контрольные: они вычисляются из остальных цифр по формулам ФНС. Для 10-значного ИНН организации девять первых цифр умножаются на веса 2, 4, 10, 3, 5, 9, 4, 6, 8, сумма берётся по модулю 11 и ещё раз по модулю 10 — результат должен совпасть с десятой цифрой.</p>
<p>Для 12-значного ИНН физлица или ИП проверяются две контрольные цифры: одиннадцатая считается с весами 7, 2, 4, 10, 3, 5, 9, 4, 6, 8 по первым десяти цифрам, двенадцатая — с весами 3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8 по первым одиннадцати.</p>
<p>Проверка подтверждает только математическую корректность номера, то есть что такой ИНН мог быть выдан. Она не гарантирует, что ИНН реально существует и принадлежит именно этой компании — для этого нужна проверка по базе ФНС. Все вычисления выполняются в вашем браузере, номер никуда не отправляется.</p>""",
  "faq": [
    ("ИНН прошёл проверку — значит, контрагент надёжный?",
     "Нет. Совпадение контрольной цифры лишь означает, что номер формально корректен. Существование ИНН и статус компании проверяйте по сервису ФНС «Прозрачный бизнес»."),
    ("Сколько цифр в ИНН ИП?",
     "Двенадцать, как у физического лица: ИП регистрируется с личным ИНН. Десятизначный ИНН бывает только у организаций."),
    ("Почему сервис пишет «недействительный», хотя номер из документов?",
     "Чаще всего это опечатка при переписывании. Если номер введён верно, а проверка не проходит — в документе может быть ошибка или подделка, стоит перепроверить по первоисточнику."),
    ("Номер куда-то отправляется при проверке?",
     "Нет. Контрольные суммы считаются локально в вашем браузере, сетевых запросов страница не выполняет."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var inEl = document.getElementById('inn-in');
  var errEl = document.getElementById('inn-error');
  var verdictEl = document.getElementById('inn-verdict');
  var typeEl = document.getElementById('inn-type');
  var checkEl = document.getElementById('inn-check');

  function checksum(digits, coeffs){
    var sum = 0;
    for (var i = 0; i < coeffs.length; i++) sum += digits[i] * coeffs[i];
    return (sum % 11) % 10;
  }

  function valid10(d){
    return checksum(d, [2, 4, 10, 3, 5, 9, 4, 6, 8]) === d[9];
  }

  function valid12(d){
    var n11 = checksum(d, [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]);
    var n12 = checksum(d, [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]);
    return n11 === d[10] && n12 === d[11];
  }

  function showError(msg){
    errEl.textContent = msg;
    errEl.classList.add('visible');
  }
  function hideError(){ errEl.classList.remove('visible'); }

  function reset(){
    verdictEl.textContent = '—';
    verdictEl.style.color = '';
    typeEl.textContent = '—';
    checkEl.textContent = '—';
  }

  function render(){
    var raw = inEl.value.replace(/[\s-]/g, '');
    if (raw === ''){ hideError(); reset(); return; }
    if (!/^\d+$/.test(raw)){
      showError('ИНН состоит только из цифр.');
      reset();
      return;
    }
    if (raw.length !== 10 && raw.length !== 12){
      showError('ИНН состоит из 10 или 12 цифр. Сейчас введено: ' + raw.length + '.');
      reset();
      return;
    }
    hideError();
    var digits = [];
    for (var i = 0; i < raw.length; i++) digits.push(raw.charCodeAt(i) - 48);
    var ok = raw.length === 10 ? valid10(digits) : valid12(digits);
    verdictEl.textContent = ok ? 'ИНН действительный' : 'ИНН недействительный';
    verdictEl.style.color = ok ? 'var(--accent)' : 'var(--danger)';
    typeEl.textContent = raw.length === 10 ? 'Организация (юрлицо)' : 'Физлицо или ИП';
    checkEl.textContent = ok ? 'сошлись' : 'не сошлись';
  }

  inEl.addEventListener('input', render);
  render();
})();
""",
  "page_css": "",
  "related": ["proverka-snils", "nalog-samozanyatyh", "strahovye-vznosy-ip", "proverka-nomera-karty"],
}
