# -*- coding: utf-8 -*-
# Генератор «рыбного» текста Lorem ipsum.

TOOL = {
  "slug": "lorem-ipsum",
  "title": "Lorem ipsum генератор",
  "meta_title": "Lorem ipsum генератор онлайн — рыбный текст",
  "meta_desc": "Сгенерируйте текст-заглушку Lorem ipsum: нужное число абзацев, предложений или слов. Классический латинский корпус, копирование в один клик.",
  "h1": "Генератор Lorem ipsum",
  "sub": "Текст-заглушка для макетов: абзацы, предложения или слова из классического латинского корпуса.",
  "category": "Генераторы",
  "fields_html": """
<div class="field-grid">
  <div class="field">
    <label for="li-count">Количество</label>
    <input type="number" id="li-count" min="1" max="100" value="3" step="1">
  </div>
  <div class="field">
    <label for="li-unit">Чего именно</label>
    <select id="li-unit">
      <option value="paragraphs" selected>абзацев</option>
      <option value="sentences">предложений</option>
      <option value="words">слов</option>
    </select>
  </div>
  <div class="field full">
    <div class="check-grid">
      <label class="check-option"><input type="checkbox" id="li-start" checked> Начать с «Lorem ipsum dolor sit amet…»</label>
    </div>
  </div>
  <div class="field full">
    <button class="btn btn-primary" id="li-gen" type="button">Сгенерировать текст</button>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Результат</div>
  <textarea id="li-out" class="li-out" rows="10" readonly></textarea>
  <div class="action-bar">
    <button class="btn btn-ghost" id="li-copy" type="button">Скопировать текст</button>
  </div>
</div>
""",
  "explain_html": """<h2>Как работает генератор рыбного текста</h2>
<p>Выберите, что считать — абзацы, предложения или отдельные слова, укажите количество и нажмите кнопку генерации. Генератор соберёт текст из классического словаря Lorem ipsum и покажет его в поле результата, откуда текст копируется одной кнопкой. Всё происходит в вашем браузере, текст никуда не отправляется.</p>
<p>Рыбный текст нужен, чтобы показать макет без настоящего содержания. Если вставить в макет осмысленный русский текст, заказчик начнёт править формулировки вместо того, чтобы смотреть на вёрстку, шрифты и отступы. Если написать «текст текст текст», длина слов получится неестественной, и блоки поведут себя иначе, чем с реальным контентом. Латинская заглушка решает обе проблемы: выглядит как настоящий текст с живой статистикой слов, но не читается и не отвлекает.</p>
<p>Словарь генератора — фрагменты трактата Цицерона «О пределах добра и зла» (45 год до н. э.), перемешанные типографами ещё в XVI веке. Из этих слов собираются предложения по 6–14 слов с заглавной буквы и точкой в конце, а абзацы — по 4–7 предложений. Случайность даёт криптографический генератор браузера crypto.getRandomValues, поэтому два запуска подряд почти наверняка выдадут разный текст.</p>
<p>Пример: вы верстаете страницу статьи и хотите заранее увидеть, как поведёт себя колонка. Запрашиваете 3 абзаца для основного текста, 12 слов для лида и одно предложение для подписи под фотографией. Через минуту макет заполнен «живым» по статистике текстом, и сразу видно, где строки переполняются, а где блок, наоборот, пустеет.</p>
<p>Скопировать результат можно кнопкой рядом с полем — текст попадёт в буфер обмена с сохранением разбивки на абзацы. Если нужен сплошной фрагмент без разбивки, запросите один большой абзац или нужное число предложений.</p>
<h3>Что выбрать: абзацы, предложения или слова</h3>
<p>Абзацы удобны для статей, карточек товаров и лендингов — они сразу дают реалистичные блоки с отступами. Предложения подходят для подзаголовков, кнопок и коротких описаний. Слова выручают там, где места совсем мало: метка, тег, пункт меню. Точное число слов полезно и для проверки обрезки текста многоточием.</p>
<ul>
<li>статья, карточка товара, лендинг — 2–4 абзаца;</li>
<li>подзаголовок или лид — 1–2 предложения;</li>
<li>кнопка, метка, тег — 2–4 слова;</li>
<li>проверка обрезки многоточием — точное число слов.</li>
</ul>
<h3>Зачем галочка «Начать с Lorem ipsum…»</h3>
<p>Классическое начало «Lorem ipsum dolor sit amet…» узнают все, кто работает с макетами: заказчик с первого взгляда понимает, что перед ним заглушка, а не черновик текста. Если нужен нейтральный вариант — скажем, для пользовательских тестов, где знакомое начало подскажет участнику, что текст неважен, — снимите галочку, и генерация начнётся со случайного места словаря.</p>
<h3>Сколько текста просить</h3>
<p>Берите объём, близкий к будущему реальному: если в статье планируется полторы тысячи знаков, сгенерируйте примерно столько же. Слишком короткая заглушка скроет проблемы с переносами и отступами, слишком длинная — раздует макет. А перед запуском сайта обязательно замените «рыбу» настоящим контентом: забытая заглушка на живой странице выглядит недоделкой.</p>
<p>Генератор не требует регистрации и работает даже без интернета после первой загрузки страницы: словарь и логика сборки лежат прямо в её коде. Это удобно, когда макет собирается в дороге или в закрытой корпоративной сети.</p>""",
  "faq": [
    ("Что вообще написано в Lorem ipsum?",
     "Это искажённые фрагменты трактата Цицерона об этике: «Нет никого, кто любил бы боль саму по себе…». Осмысленной латынью текст не является — слова и окончания перемешаны."),
    ("Почему нельзя просто написать «текст текст текст»?",
     "Повторяющиеся слова дают неестественную плотность и длину строк — вёрстка на реальном контенте «поедет». Lorem ipsum имитирует статистику настоящего текста."),
    ("Есть ли ограничения на объём?",
     "До 100 абзацев, предложений или слов за раз. Для больших объёмов сгенерируйте несколько порций."),
    ("Можно ли использовать этот текст в продакшене?",
     "Технически — да, но не стоит: «рыба» на живом сайте выглядит как недоделка и сбивает посетителей. Используйте только на этапе макета."),
    ("Кто придумал Lorem ipsum?",
     "Основа — трактат Цицерона «О пределах добра и зла», написанный в 45 году до н. э. Слова перемешали типографы XVI века, а в нынешнем виде текст разошёлся в 1960-х вместе с листами для вёрстки Letraset."),
    ("Работает ли генератор без интернета?",
     "Да. Словарь и логика сборки находятся в коде страницы и выполняются в браузере, поэтому после первой загрузки интернет не нужен."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var WORDS = ('lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor ' +
    'incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud ' +
    'exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure ' +
    'in reprehenderit voluptate velit esse cillum eu fugiat nulla pariatur excepteur ' +
    'sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim ' +
    'id est laborum').split(' ');
  var START = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.';

  var countEl = document.getElementById('li-count');
  var unitEl = document.getElementById('li-unit');
  var startEl = document.getElementById('li-start');
  var genBtn = document.getElementById('li-gen');
  var outEl = document.getElementById('li-out');
  var copyBtn = document.getElementById('li-copy');

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

  function rnd(n){
    var buf = new Uint32Array(1);
    crypto.getRandomValues(buf);
    return buf[0] % n;
  }
  function word(){ return WORDS[rnd(WORDS.length)]; }

  function sentence(){
    var n = 6 + rnd(9);
    var parts = [];
    for (var i = 0; i < n; i++) parts.push(word());
    var s = parts.join(' ');
    return s.charAt(0).toUpperCase() + s.slice(1) + '.';
  }

  function paragraph(){
    var n = 4 + rnd(4);
    var parts = [];
    for (var i = 0; i < n; i++) parts.push(sentence());
    return parts.join(' ');
  }

  function withStart(text){
    if (!startEl.checked) return text;
    var dot = text.indexOf('.');
    if (dot < 0) return START;
    return START + text.slice(dot + 1);
  }

  function generate(){
    var count = parseInt(countEl.value, 10);
    if (isNaN(count) || count < 1) count = 3;
    if (count > 100) count = 100;
    var unit = unitEl.value;
    var out;
    if (unit === 'paragraphs'){
      var paras = [];
      for (var i = 0; i < count; i++) paras.push(paragraph());
      out = withStart(paras.join('\n\n'));
    } else if (unit === 'sentences'){
      var sents = [];
      for (var j = 0; j < count; j++) sents.push(sentence());
      out = withStart(sents.join(' '));
    } else {
      var words = [];
      for (var k = 0; k < count; k++) words.push(word());
      var body = words.join(' ');
      if (startEl.checked && count >= 5){
        var tail = words.slice(5).join(' ');
        body = tail ? 'lorem ipsum dolor sit amet ' + tail : 'lorem ipsum dolor sit amet';
      }
      out = body.charAt(0).toUpperCase() + body.slice(1) + '.';
    }
    outEl.value = out;
  }

  genBtn.addEventListener('click', generate);
  copyBtn.addEventListener('click', function(){ copyText(outEl.value, copyBtn); });
  generate();
})();
""",
  "page_css": ".li-out{width:100%;margin:10px 0 4px;padding:12px 13px;border-radius:10px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);font-family:var(--font-body);font-size:.92rem;line-height:1.55;resize:vertical;}",
  "related": ["schetchik-slov", "generator-nikneimov", "sluchaynye-chisla", "uuid-generator"],
}
