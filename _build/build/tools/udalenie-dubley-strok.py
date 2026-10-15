# -*- coding: utf-8 -*-
# Удаление дублей строк с опциями регистра, trim и пустых строк.

TOOL = {
  "slug": "udalenie-dubley-strok",
  "title": "Удаление дублей строк",
  "meta_title": "Удаление дублей строк онлайн — очистка списка",
  "meta_desc": "Уберите повторяющиеся строки из списка: с игнорированием регистра, обрезкой пробелов и удалением пустых строк. Порядок первых вхождений сохраняется.",
  "h1": "Удаление дублей строк",
  "sub": "Очистите список от повторов: порядок сохраняется, дубли и пустые строки исчезают.",
  "category": "Текст",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <label for="dd-in">Строки, по одной на строку</label>
    <textarea id="dd-in" rows="8" placeholder="яблоко&#10;груша&#10;Яблоко&#10;&#10;груша"></textarea>
  </div>
  <div class="field full">
    <div class="check-grid">
      <label class="check-option"><input type="checkbox" id="dd-ci"> Не учитывать регистр</label>
      <label class="check-option"><input type="checkbox" id="dd-trim" checked> Обрезать пробелы по краям</label>
      <label class="check-option"><input type="checkbox" id="dd-empty" checked> Удалить пустые строки</label>
    </div>
  </div>
  <div class="field full">
    <button class="btn btn-primary" id="dd-run" type="button">Удалить дубли</button>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Осталось строк</div>
  <div class="r-value" id="dd-left">—</div>
  <div class="r-rows">
    <div><b id="dd-total">—</b><span>было строк</span></div>
    <div><b id="dd-dups">—</b><span>удалено дублей</span></div>
    <div><b id="dd-empty-n">—</b><span>удалено пустых</span></div>
  </div>
  <textarea id="dd-out" class="dd-out" rows="7" readonly placeholder="Здесь появится очищенный список"></textarea>
  <div class="action-bar">
    <button class="btn btn-ghost" id="dd-copy" type="button">Скопировать результат</button>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Инструмент идёт по строкам сверху вниз и оставляет только первое вхождение каждой строки — порядок в списке не меняется. Дубль определяется сравнением строк: с включённой опцией «не учитывать регистр» строки «Яблоко» и «яблоко» считаются одинаковыми, и остаётся та, что встретилась первой.</p>
<p>Обрезка пробелов убирает пробелы и табуляции в начале и конце каждой строки до сравнения: « слово» и «слово » станут одной строкой. Удаление пустых строк вычищает строки, которые пусты или состоят только из пробелов (после обрезки).</p>
<p>Обработка выполняется локально в браузере, текст никуда не отправляется. Списки в сотни тысяч строк обрабатываются мгновенно — сравнение идёт через хеш-таблицу, а не попарным перебором.</p>""",
  "faq": [
    ("Останется ли порядок строк как в исходном списке?",
     "Да. Удаляются только повторные вхождения, первое вхождение каждой строки остаётся на своём месте. Сортировка не выполняется."),
    ("Как сравнить два списка, а не очистить один?",
     "Для этого есть отдельный инструмент «Сравнение списков» — он покажет пересечение и различия двух списков."),
    ("«Яблоко» и «яблоко» — это дубли?",
     "По умолчанию нет: сравнение учитывает регистр. Включите опцию «Не учитывать регистр», и такие строки будут считаться одинаковыми."),
    ("Что считается пустой строкой?",
     "Строка без символов или состоящая только из пробелов и табуляций. Если опция обрезки пробелов включена, такие строки удаляются вместе с дублями."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var inEl = document.getElementById('dd-in');
  var outEl = document.getElementById('dd-out');
  var runBtn = document.getElementById('dd-run');
  var copyBtn = document.getElementById('dd-copy');
  var ciEl = document.getElementById('dd-ci');
  var trimEl = document.getElementById('dd-trim');
  var emptyEl = document.getElementById('dd-empty');
  var totalEl = document.getElementById('dd-total');
  var dupsEl = document.getElementById('dd-dups');
  var emptyNEl = document.getElementById('dd-empty-n');
  var leftEl = document.getElementById('dd-left');

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

  function run(){
    if (inEl.value === ''){
      outEl.value = '';
      totalEl.textContent = '0';
      dupsEl.textContent = '0';
      emptyNEl.textContent = '0';
      leftEl.textContent = '0';
      return;
    }
    var lines = inEl.value.split(/\r\n|\r|\n/);
    var seen = {};
    var kept = [];
    var dups = 0;
    var empties = 0;
    for (var i = 0; i < lines.length; i++){
      var line = lines[i];
      if (trimEl.checked) line = line.replace(/^\s+|\s+$/g, '');
      if (line === '' && emptyEl.checked){ empties++; continue; }
      var key = ciEl.checked ? line.toLowerCase() : line;
      if (Object.prototype.hasOwnProperty.call(seen, key)){ dups++; continue; }
      seen[key] = true;
      kept.push(line);
    }
    outEl.value = kept.join('\n');
    totalEl.textContent = window.formatMoney(lines.length);
    dupsEl.textContent = window.formatMoney(dups);
    emptyNEl.textContent = window.formatMoney(empties);
    leftEl.textContent = window.formatMoney(kept.length);
  }

  runBtn.addEventListener('click', run);
  copyBtn.addEventListener('click', function(){ copyText(outEl.value, copyBtn); });
  [ciEl, trimEl, emptyEl].forEach(function(el){
    el.addEventListener('change', function(){ if (inEl.value !== '') run(); });
  });
})();
""",
  "page_css": ".dd-out{width:100%;margin:14px 0 4px;padding:12px 13px;border-radius:10px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);font-family:var(--font-mono);font-size:.9rem;resize:vertical;}",
  "related": ["schetchik-slov", "transliteraciya", "sravnenie-spiskov", "peremeshat-spisok"],
}
