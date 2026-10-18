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
  "explain_html": """<h2>Как убрать повторяющиеся строки из списка</h2>
<p>Вставьте список в поле — по одному элементу на строку — и нажмите кнопку очистки. Инструмент пройдёт по строкам сверху вниз и оставит только первое вхождение каждой: повторы исчезнут, порядок сохранится. Перед сравнением можно включить обрезку пробелов, игнорирование регистра и удаление пустых строк. Результат копируется одной кнопкой или скачивается файлом.</p>
<p>Дубль — это строка, которая уже встречалась выше. Сравнение идёт через хеш-таблицу: каждая новая строка проверяется против уже увиденных за доли секунды, поэтому списки в сотни тысяч строк обрабатываются мгновенно, без попарного перебора. Первое вхождение всегда остаётся на своём месте, удаляются только повторные — сортировка не выполняется.</p>
<p>Три опции меняют то, что считается «одинаковым». Обрезка пробелов убирает пробелы и табуляции по краям строки до сравнения: « слово» и «слово » станут одной строкой. Игнорирование регистра приравнивает «Яблоко» и «яблоко» — останется вариант, который встретился первым. Удаление пустых строк вычищает строки без символов или состоящие только из пробелов.</p>
<p>Пример: список «молоко, хлеб, молоко, Сыр, сыр, хлеб». Без опций останется «молоко, хлеб, Сыр, сыр» — регистр различает два «сыра». С включённым игнорированием регистра останется «молоко, хлеб, Сыр»: строка «сыр» в нижнем регистре сочтётся дублём «Сыр» и пропадёт.</p>
<h3>Откуда в списках берутся дубли</h3>
<p>Повторы появляются почти всегда при склейке данных из разных мест:</p>
<ul>
<li>объединение баз клиентов из CRM, почтовой рассылки и таблицы Excel;</li>
<li>выгрузки, где один заказ или товар попадает в отчёт дважды;</li>
<li>списки ключевых слов, собранные из нескольких подборщиков;</li>
<li>email-рассылки, куда адрес попал и вручную, и из импорта.</li>
</ul>
<p>Ручная чистка таких списков — часы работы и гарантированные пропуски. Автоматическая очистка снимает задачу за секунду: вставили, проверили счётчик, скопировали.</p>
<h3>Что именно считается дублём</h3>
<p>Строки сравниваются целиком, посимвольно. «Иванов И.» и «Иванов И» — разные строки, как и «10» и «10,0». Невидимые символы тоже участвуют в сравнении: пробел в конце строки делает её отличной от такой же без пробела. Если список собран копипастой из разных источников, сначала включите обрезку пробелов — она убирает большинство таких ложных «недублей».</p>
<h3>Регистр: когда разные строки на самом деле одинаковые</h3>
<p>По умолчанию сравнение строгое: «Apple» и «apple» — две разные строки. Для email-адресов, доменов и тегов это часто нежелательно — там регистр значения не имеет. Включите опцию «Не учитывать регистр»: сравнение пойдёт без учёта заглавных, а в результате останется написание первого вхождения. Для имён собственных, где регистр важен, опцию лучше не трогать.</p>
<h3>Как не потерять данные</h3>
<p>Инструмент не меняет исходный текст: он показывает очищенную копию, а поле ввода остаётся нетронутым, пока вы его не перезапишете. Перед копированием результата сверьтесь со счётчиком — он показывает, сколько строк было и сколько стало. Разница между этими числами и есть количество найденных дублей: если их подозрительно мало, скорее всего, строки отличаются невидимыми пробелами или регистром. В таком случае попробуйте другую комбинацию опций и сравните счётчик ещё раз.</p>""",
  "faq": [
    ("Останется ли порядок строк как в исходном списке?",
     "Да. Удаляются только повторные вхождения, первое вхождение каждой строки остаётся на своём месте. Сортировка не выполняется."),
    ("Как сравнить два списка, а не очистить один?",
     "Для этого есть отдельный инструмент «Сравнение списков» — он покажет пересечение и различия двух списков."),
    ("«Яблоко» и «яблоко» — это дубли?",
     "По умолчанию нет: сравнение учитывает регистр. Включите опцию «Не учитывать регистр», и такие строки будут считаться одинаковыми."),
    ("Что считается пустой строкой?",
     "Строка без символов или состоящая только из пробелов и табуляций. Такие строки убирает отдельная опция «Удалить пустые строки» — у неё свой счётчик; обрезка пробелов сама по себе пустые строки не удаляет."),
    ("А если нужны сами дубли, а не уникальный список?",
     "Этот инструмент показывает счётчик удалённых строк, но не выводит их списком. Чтобы увидеть, что именно повторялось, очистите список и сравните результат с исходником в инструменте «Сравнение списков»."),
    ("Текст списка куда-то отправляется?",
     "Нет. Обработка выполняется локально в вашем браузере, данные не покидают устройство и нигде не сохраняются."),
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
