# -*- coding: utf-8 -*-
# Транслитерация RU → LAT с режимом slug для URL.

TOOL = {
  "slug": "transliteraciya",
  "title": "Транслитерация",
  "meta_title": "Транслитерация онлайн — кириллица в латиницу",
  "meta_desc": "Переведите русский текст в латиницу: ж → zh, х → kh, щ → shch. Режим «для URL» делает готовый slug: строчные буквы и дефисы.",
  "h1": "Транслитерация текста",
  "sub": "Русский текст латиницей — с сохранением регистра или готовым slug для ссылок.",
  "category": "Текст",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <label for="tr-in">Текст на русском</label>
    <textarea id="tr-in" rows="6" placeholder="Привет, мир!"></textarea>
  </div>
  <div class="field full">
    <div class="check-grid">
      <label class="check-option"><input type="checkbox" id="tr-slug"> Для URL: slug строчными буквами через дефис</label>
    </div>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Результат латиницей</div>
  <textarea id="tr-out" class="tr-out" rows="4" readonly></textarea>
  <div class="action-bar">
    <button class="btn btn-primary" id="tr-copy" type="button">Скопировать</button>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Таблица соответствия близка к ГОСТ Р 7.0.34-2014: ж → zh, х → kh, ц → ts, ч → ch, ш → sh, щ → shch, ы → y, э → e, ю → yu, я → ya, ё → e, мягкий и твёрдый знаки опускаются. Регистр сохраняется: «Москва» превратится в «Moskva», а не в «moskva».</p>
<p>Режим «для URL» делает из фразы готовый slug: всё приводится к нижнему регистру, пробелы и любые посторонние символы заменяются дефисами, повторные дефисы схлопываются, а дефисы по краям обрезаются. Такие адреса лучше читаются людьми и одинаково понятны поисковикам.</p>
<p>Учтите, что официальные документы используют другие стандарты: в загранпаспортах ё превращается в e, а и — в i по тем же правилам, но «й» там — i, а не y. Для документов сверяйтесь с правилами конкретного ведомства, а для сайтов, почты и никнеймов этой таблицы достаточно.</p>""",
  "faq": [
    ("Чем этот вариант отличается от транслитерации в загранпаспорте?",
     "В заграничных документах действует стандарт ИКАО: й → i, ь и ъ опускаются, ы → i. У нас — таблица в духе ГОСТ Р 7.0.34-2014, которая удобнее для веба: й → y, ы → y."),
    ("Куда пропадают мягкий и твёрдый знаки?",
     "Они не передаются на письме латиницей по выбранной таблице, поэтому просто опускаются: «подъезд» → «podezd», «соль» → «sol»."),
    ("Что делает режим «для URL»?",
     "Приводит результат к нижнему регистру, заменяет пробелы и все символы, кроме латинских букв и цифр, на дефисы и убирает лишние дефисы. Получается готовый slug вида «privet-mir»."),
    ("Почему «ё» превращается в «e», а не в «yo»?",
     "В ГОСТ-подобной таблице для веб-адресов принято «e»: так slug короче и не конфликтует с «е». Если нужен вариант с «yo», замените вручную после копирования."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var MAP = {
    'а':'a', 'б':'b', 'в':'v', 'г':'g', 'д':'d', 'е':'e', 'ё':'e', 'ж':'zh',
    'з':'z', 'и':'i', 'й':'y', 'к':'k', 'л':'l', 'м':'m', 'н':'n', 'о':'o',
    'п':'p', 'р':'r', 'с':'s', 'т':'t', 'у':'u', 'ф':'f', 'х':'kh', 'ц':'ts',
    'ч':'ch', 'ш':'sh', 'щ':'shch', 'ъ':'', 'ы':'y', 'ь':'', 'э':'e', 'ю':'yu', 'я':'ya'
  };

  var inEl = document.getElementById('tr-in');
  var outEl = document.getElementById('tr-out');
  var slugEl = document.getElementById('tr-slug');
  var copyBtn = document.getElementById('tr-copy');

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

  function translit(text){
    var out = '';
    for (var i = 0; i < text.length; i++){
      var ch = text.charAt(i);
      var low = ch.toLowerCase();
      if (Object.prototype.hasOwnProperty.call(MAP, low)){
        var rep = MAP[low];
        if (ch !== low && rep !== '') rep = rep.charAt(0).toUpperCase() + rep.slice(1);
        out += rep;
      } else {
        out += ch;
      }
    }
    return out;
  }

  function toSlug(text){
    return translit(text).toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/-{2,}/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function render(){
    var src = inEl.value;
    outEl.value = slugEl.checked ? toSlug(src) : translit(src);
  }

  copyBtn.addEventListener('click', function(){ copyText(outEl.value, copyBtn); });
  inEl.addEventListener('input', render);
  slugEl.addEventListener('change', render);
  render();
})();
""",
  "page_css": ".tr-out{width:100%;margin:10px 0 4px;padding:12px 13px;border-radius:10px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);font-family:var(--font-mono);font-size:.95rem;resize:vertical;}",
  "related": ["schetchik-slov", "udalenie-dubley-strok", "generator-nikneimov", "summa-propisyu"],
}
