# -*- coding: utf-8 -*-
# Генератор UUID v4 на crypto.getRandomValues.

TOOL = {
  "slug": "uuid-generator",
  "title": "Генератор UUID",
  "meta_title": "Генератор UUID v4 онлайн — до 50 штук за раз",
  "meta_desc": "Сгенерируйте UUID версии 4: криптографически стойкий random, до 50 идентификаторов за раз, копирование в один клик.",
  "h1": "Генератор UUID",
  "sub": "Криптографически стойкие UUID версии 4 — от одного до пятидесяти штук за раз.",
  "category": "Генераторы",
  "fields_html": """
<div class="field-grid">
  <div class="field">
    <label for="uu-count">Количество (1–50)</label>
    <input type="number" id="uu-count" min="1" max="50" value="5" step="1">
  </div>
  <div class="field">
    <label>Действие</label>
    <button class="btn btn-primary" id="uu-gen" type="button">Сгенерировать</button>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">UUID версии 4 — клик по строке копирует её</div>
  <ul class="uuid-list" id="uu-list"></ul>
  <div class="action-bar">
    <button class="btn btn-ghost" id="uu-more" type="button">Ещё</button>
    <button class="btn btn-ghost" id="uu-copy" type="button">Скопировать все</button>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>UUID версии 4 — это 122 случайных бита, оформленные в привычный вид 8-4-4-4-12 шестнадцатеричных цифр: например, 3f6b2a41-…-…. Ещё 6 бит заняты служебными метками версии (4) и варианта (RFC 4122). Генератор использует crypto.getRandomValues — криптографический источник случайности браузера, а не Math.random, который для идентификаторов не предназначен.</p>
<p>Вероятность совпадения двух UUID v4 ничтожна: чтобы шанс коллизии достиг 50%, нужно сгенерировать около 2,7 квинтиллиона идентификаторов. Именно поэтому UUID используют как первичные ключи в распределённых системах — без всякой централизации и координации.</p>
<p>Генерация происходит локально в вашем браузере, идентификаторы никуда не отправляются. Если нужны UUID других версий (1, 6, 7 — с меткой времени), этот инструмент не подойдёт: здесь только версия 4.</p>""",
  "faq": [
    ("Чем UUID v4 отличается от v7?",
     "V4 — чистая случайность. V7 кодирует в начало метку времени, поэтому идентификаторы сортируются по времени создания и дружелюбнее к индексам баз данных. Здесь генерируется только v4."),
    ("Насколько надёжна генерация?",
     "Используется crypto.getRandomValues — тот же генератор, что браузер применяет для ключей шифрования. Math.random не используется вовсе."),
    ("Могут ли два сгенерированных UUID совпасть?",
     "Теоретически да, практически — нет: при миллиарде UUID в секунду столетие генерации даст шанс одной коллизии порядка 50%. Для любых прикладных задач риском пренебрегают."),
    ("Что делает кнопка «Ещё»?",
     "Генерирует новую порцию идентификаторов взамен текущей — в том же количестве, что указано в поле."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var countEl = document.getElementById('uu-count');
  var genBtn = document.getElementById('uu-gen');
  var moreBtn = document.getElementById('uu-more');
  var copyBtn = document.getElementById('uu-copy');
  var listEl = document.getElementById('uu-list');
  var current = [];

  function copyText(text, btn){
    function done(){
      if (!btn) return;
      var prev = btn.textContent;
      btn.textContent = 'Скопировано!';
      setTimeout(function(){ btn.textContent = prev; }, 1500);
    }
    function fallback(){
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta);
      done();
    }
    if (navigator.clipboard && window.isSecureContext){
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  function randomUuid(){
    var buf = new Uint8Array(16);
    crypto.getRandomValues(buf);
    buf[6] = (buf[6] & 15) | 64;    // версия 4
    buf[8] = (buf[8] & 63) | 128;   // вариант RFC 4122
    var parts = [];
    for (var i = 0; i < 16; i++){
      var h = buf[i].toString(16);
      parts.push(h.length === 1 ? '0' + h : h);
    }
    return parts.slice(0, 4).join('') + '-' + parts.slice(4, 6).join('') + '-' +
           parts.slice(6, 8).join('') + '-' + parts.slice(8, 10).join('') + '-' +
           parts.slice(10, 16).join('');
  }

  function getCount(){
    var n = parseInt(countEl.value, 10);
    if (isNaN(n)) return 5;
    if (n < 1) return 1;
    if (n > 50) return 50;
    return n;
  }

  function renderList(){
    listEl.textContent = '';
    current.forEach(function(id){
      var li = document.createElement('li');
      li.textContent = id;
      li.title = 'Нажмите, чтобы скопировать';
      li.addEventListener('click', function(){ copyText(id, null); });
      listEl.appendChild(li);
    });
  }

  function generate(){
    var n = getCount();
    current = [];
    for (var i = 0; i < n; i++) current.push(randomUuid());
    renderList();
  }

  genBtn.addEventListener('click', generate);
  moreBtn.addEventListener('click', generate);
  copyBtn.addEventListener('click', function(){
    if (current.length) copyText(current.join('\n'), copyBtn);
  });
  generate();
})();
""",
  "page_css": ".uuid-list{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:6px}.uuid-list li{font-family:var(--font-mono);font-size:.92rem;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:9px 12px;cursor:pointer;word-break:break-all;transition:border-color .15s ease,color .15s ease}.uuid-list li:hover{border-color:var(--accent);color:var(--accent)}",
  "related": ["generator-paroley", "generator-promokodov", "generator-nikneimov", "sluchaynye-chisla"],
}
