# -*- coding: utf-8 -*-
# Генератор никнеймов: прилагательное + существительное, ru/lat, цифры.

TOOL = {
  "slug": "generator-nikneimov",
  "title": "Генератор никнеймов",
  "meta_title": "Генератор никнеймов онлайн — русские и английские",
  "meta_desc": "Подберите никнейм: прилагательное и существительное на русском или латиницей, цифры по желанию. 10 вариантов за раз, клик копирует ник.",
  "h1": "Генератор никнеймов",
  "sub": "Десять готовых ников за раз: русские или латиницей, с цифрами или без.",
  "category": "Генераторы",
  "fields_html": """
<div class="field-grid">
  <div class="field">
    <label for="nk-lang">Язык</label>
    <select id="nk-lang">
      <option value="ru" selected>Русский</option>
      <option value="en">Латиница</option>
      <option value="mix">Смешанный</option>
    </select>
  </div>
  <div class="field">
    <label for="nk-len">Длина</label>
    <select id="nk-len">
      <option value="short">Короткий: только существительное</option>
      <option value="medium" selected>Средний: прилагательное + существительное</option>
      <option value="long">Длинный: прилагательное + два существительных</option>
    </select>
  </div>
  <div class="field full">
    <div class="check-grid">
      <label class="check-option"><input type="checkbox" id="nk-digits"> Добавить две цифры в конец</label>
    </div>
  </div>
  <div class="field full">
    <button class="btn btn-primary" id="nk-gen" type="button">Сгенерировать 10 вариантов</button>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Варианты — клик по нику копирует его</div>
  <ul class="nick-list" id="nk-list"></ul>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Ник собирается из двух словарей: прилагательных (Тёмный, Стальной, Silent, Iron) и существительных (Волк, Ворон, Falcon, Shadow). Каждая генерация выдаёт десять уникальных сочетаний; случайный выбор выполняется через crypto.getRandomValues — криптографический генератор браузера, а не Math.random.</p>
<p>Короткий вариант — одно существительное, средний — прилагательное плюс существительное в верблюжьем регистре (ТёмныйВолк, SilentFox), длинный добавляет второе существительное. Опция с цифрами дописывает в конец число от 10 до 99 — это выручает, когда красивый ник уже занят.</p>
<p>Русские ники подходят для чатов и игр, латиница — для сервисов, где разрешены только английские буквы. Смешанный режим берёт язык для каждого слова случайно, так что получаются комбинации вроде ТёмныйFalcon — иногда именно такие самые свободные.</p>""",
  "faq": [
    ("Ники уникальные? Можно сразу регистрировать?",
     "Генератор собирает случайные сочетания слов и не проверяет занятость. Перед регистрацией проверьте ник в самом сервисе — или добавьте цифры, это резко повышает шансы, что ник свободен."),
    ("Почему ники пишутся слитно и с заглавными?",
     "Верблюжий регистр (ТёмныйВолк) читается лучше слитного нижнего и при этом допустим почти везде. Если сервис не принимает заглавные, просто напишите ник строчными."),
    ("Как получить ник с подчёркиваниями или дефисами?",
     "Скопируйте вариант и вставьте разделитель вручную между словами: Тёмный_Волк или Silent-Fox. Такие символы разрешены не везде, поэтому по умолчанию их нет."),
    ("Сколько всего возможных сочетаний?",
     "В каждом словаре по 24 слова. Средний вариант даёт 24 × 24 = 576 сочетаний на язык, длинный — больше 13 тысяч, а с цифрами количество умножается ещё на 90."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var ADJ_RU = ['Тёмный','Быстрый','Тихий','Дерзкий','Лунный','Северный','Стальной','Хитрый','Весёлый','Мрачный','Летний','Дикий','Смелый','Холодный','Яркий','Мудрый','Древний','Ночной','Огненный','Ледяной','Вольный','Грозный','Южный','Звёздный'];
  var NOUN_RU = ['Волк','Лис','Ворон','Тигр','Медведь','Сокол','Олень','Енот','Барс','Кот','Ёж','Заяц','Дракон','Феникс','Призрак','Странник','Охотник','Вождь','Маг','Шаман','Рыцарь','Пират','Следопыт','Хранитель'];
  var ADJ_EN = ['Dark','Swift','Silent','Bold','Lunar','North','Steel','Sly','Merry','Grim','Wild','Cold','Bright','Ancient','Night','Fire','Ice','Free','Storm','Iron','Golden','Crimson','Hollow','Ember'];
  var NOUN_EN = ['Wolf','Fox','Raven','Tiger','Bear','Falcon','Deer','Cat','Dragon','Phoenix','Ghost','Wanderer','Hunter','Mage','Knight','Pirate','Ranger','Keeper','Shadow','Storm','Viper','Sage','Nomad','Warden'];

  var langEl = document.getElementById('nk-lang');
  var lenEl = document.getElementById('nk-len');
  var digitsEl = document.getElementById('nk-digits');
  var genBtn = document.getElementById('nk-gen');
  var listEl = document.getElementById('nk-list');

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
  function pick(arr){ return arr[rnd(arr.length)]; }

  function oneNick(){
    var lang = langEl.value;
    var ru = lang === 'ru' || (lang === 'mix' && rnd(2) === 0);
    var adj = ru ? pick(ADJ_RU) : pick(ADJ_EN);
    var noun = ru ? pick(NOUN_RU) : pick(NOUN_EN);
    var len = lenEl.value;
    var base;
    if (len === 'short'){
      base = noun;
    } else if (len === 'long'){
      var ru2 = lang === 'ru' || (lang === 'mix' && rnd(2) === 0);
      var noun2 = ru2 ? pick(NOUN_RU) : pick(NOUN_EN);
      var guard = 0;
      while (noun2 === noun && guard < 10){ noun2 = ru2 ? pick(NOUN_RU) : pick(NOUN_EN); guard++; }
      base = adj + noun + noun2;
    } else {
      base = adj + noun;
    }
    if (digitsEl.checked) base += String(10 + rnd(90));
    return base;
  }

  function generate(){
    listEl.textContent = '';
    var seen = {};
    var added = 0;
    var guard = 0;
    while (added < 10 && guard < 200){
      guard++;
      var nick = oneNick();
      if (Object.prototype.hasOwnProperty.call(seen, nick)) continue;
      seen[nick] = true;
      var li = document.createElement('li');
      li.textContent = nick;
      li.title = 'Нажмите, чтобы скопировать';
      (function(n){
        li.addEventListener('click', function(){ copyText(n, null); });
      })(nick);
      listEl.appendChild(li);
      added++;
    }
  }

  genBtn.addEventListener('click', generate);
  [langEl, lenEl].forEach(function(el){ el.addEventListener('change', generate); });
  digitsEl.addEventListener('change', generate);
  generate();
})();
""",
  "page_css": ".nick-list{list-style:none;margin:12px 0 0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:6px}.nick-list li{font-family:var(--font-mono);font-size:.95rem;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;cursor:pointer;word-break:break-all;transition:border-color .15s ease,color .15s ease}.nick-list li:hover{border-color:var(--accent);color:var(--accent)}@media (max-width:640px){.nick-list{grid-template-columns:1fr}}",
  "related": ["generator-paroley", "uuid-generator", "sluchaynye-chisla", "lorem-ipsum"],
}
