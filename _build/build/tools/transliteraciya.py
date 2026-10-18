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
  "explain_html": """<h2>Как кириллица превращается в латиницу</h2>
<p>Введите русский текст в поле — транслитератор заменит каждую букву по таблице соответствия и сразу покажет результат латиницей. Регистр сохраняется, цифры и знаки препинания не трогаются. Если нужен адрес для страницы сайта, включите режим «для URL»: получите готовый slug в нижнем регистре с дефисами вместо пробелов. Результат копируется одной кнопкой.</p>
<p>Основа — таблица замен, близкая к ГОСТ Р 7.0.34-2014. Односимвольные замены очевидны: а → a, б → b, в → v. Интереснее буквы, которых нет в латинском алфавите: ж → zh, х → kh, ц → ts, ч → ch, ш → sh, щ → shch, ы → y, э → e, ю → yu, я → ya. Буква «ё» превращается в «e», а мягкий и твёрдый знаки латиницей не передаются и просто опускаются.</p>
<p>Замена идёт посимвольно слева направо, поэтому регистр исходника полностью повторяется: «Москва» станет «Moskva», а «МОСКВА» — «MOSKVA». Это удобно для имён и названий, где заглавная буква имеет значение. Если нужен однородный нижний регистр — это как раз делает режим «для URL».</p>
<p>Пример: фраза «Привет, мир!» превращается в «Privet, mir!» — запятая и восклицательный знак остаются на месте. В режиме «для URL» та же фраза даст «privet-mir»: всё приведено к нижнему регистру, пробелы и знаки препинания заменены дефисами, повторные дефисы схлопнуты, крайние — обрезаны. Фамилия «Щербаков» станет «Shcherbakov», а «подъезд» — «podezd».</p>
<h3>Где транслит нужен чаще всего</h3>
<p>Типичные задачи, с которыми сюда приходят:</p>
<ul>
<li>адреса страниц: заголовок статьи превращается в slug вида «kak-vybrat-ipoteku»;</li>
<li>имена файлов и папок, где кириллица ломает ссылки или архивы;</li>
<li>логины, почта и никнеймы в сервисах, не принимающих русские буквы;</li>
<li>написание имён и фамилий латиницей для зарубежных коллег;</li>
<li>сокращение SMS: латиница вмещает 160 символов против 70 для кириллицы.</li>
</ul>
<p>Во всех случаях, кроме официальных документов, таблицы этой страницы достаточно.</p>
<h3>Чем транслит для веба отличается от транслита в документах</h3>
<p>Единого стандарта нет, и это главный источник путаницы. В загранпаспортах действуют правила ИКАО: й → i, ы → y, ь и ъ опускаются. В банковских картах и международных переводах — свои таблицы. Здесь используется упрощённый вариант, удобный для сайтов, почты и никнеймов: й → y, ы → y. Для официальных бумаг сверяйтесь с требованиями конкретного ведомства, а не с любым онлайн-транслитом.</p>
<h3>Почему «е» и «ё» дают одинаковую латиницу</h3>
<p>Обе буквы превращаются в «e» — так короче, и slug не конфликтует сам с собой: «тёмный» и «темный» дадут одинаковый «temny». Если для вас принципиально отличие «ё» — например, в фамилии, — замените «e» на «yo» вручную после копирования.</p>
<h3>Когда одна буква превращается в четыре</h3>
<p>Составные замены удлиняют слово: щ → shch — это четыре латинских символа вместо одной кириллической. Поэтому «борщ» — это «borshch» из семи знаков. Учитывайте это, если транслит идёт в поле с ограничением длины: домен, логин или имя файла. Для коротких адресов длинные слова иногда разумно сократить вручную.</p>""",
  "faq": [
    ("Чем этот вариант отличается от транслитерации в загранпаспорте?",
     "В заграничных документах действует стандарт ИКАО: й → i, ы → y, ь и ъ опускаются. У нас — упрощённая таблица для веба и URL: й → y, остальные замены близки к ИКАО."),
    ("Куда пропадают мягкий и твёрдый знаки?",
     "Они не передаются на письме латиницей по выбранной таблице, поэтому просто опускаются: «подъезд» → «podezd», «соль» → «sol»."),
    ("Что делает режим «для URL»?",
     "Приводит результат к нижнему регистру, заменяет пробелы и все символы, кроме латинских букв и цифр, на дефисы и убирает лишние дефисы. Получается готовый slug вида «privet-mir»."),
    ("Почему «ё» превращается в «e», а не в «yo»?",
     "В ГОСТ-подобной таблице для веб-адресов принято «e»: так slug короче и не конфликтует с «е». Если нужен вариант с «yo», замените вручную после копирования."),
    ("Работает ли транслитерация в обратную сторону?",
     "Нет, преобразование необратимо: «e» могла получиться и из «е», и из «ё» или «э». Восстановить исходное русское написание по латинице однозначно нельзя."),
    ("Можно ли транслитерировать большой текст?",
     "Да, ограничений по объёму нет: обработка идёт локально в браузере, текст никуда не отправляется. Вставляйте хоть целую статью — результат появится мгновенно."),
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
