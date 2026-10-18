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
  "explain_html": """<h2>Как работает генератор UUID v4</h2>
<p>Нажмите кнопку — и получите порцию случайных идентификаторов стандарта RFC 4122. Каждый UUID v4 — это 128 бит, из которых 122 бита случайны, а 6 заняты служебными метками версии и варианта. Случайность даёт crypto.getRandomValues — криптографический генератор браузера. Всё происходит локально: идентификаторы не покидают ваш компьютер.</p>
<p>Привычная запись 8-4-4-4-12 — это 32 шестнадцатеричные цифры, разбитые дефисами на пять групп:</p>
<p><code>xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx</code></p>
<p>Цифра 4 в начале третьей группы — метка версии. Первый символ четвёртой группы (y) принимает значения 8, 9, a или b — это метка варианта. Всё остальное — чистая случайность, Math.random здесь не используется вовсе.</p>
<p>О вероятности коллизий судит парадокс дней рождения: совпадения возможны задолго до перебора всех вариантов. Но пространство в 2¹²² настолько велико, что для шанса коллизии в 50% потребуется сгенерировать около 2,7 квинтиллиона UUID. При миллиарде идентификаторов в секунду на это ушло бы около 85 лет. Практическим риском пренебрегают. Для пачки в тысячу идентификаторов вероятность совпадения хотя бы одной пары — порядка одной квинтиллионной.</p>
<p>Пример: вы создаёте заказ в базе на одном сервере, а коллега — на другом. С автоинкрементом ключи столкнулись бы при слиянии. С UUID v4 каждый получает свой идентификатор вида 3f6b2a41-9c5e-4d1f-8a2b-7e0c4f6d8a91 — и никакой координации между серверами не нужно. Так же работают офлайн-приложения: запись, созданная без интернета, получает свой UUID и при синхронизации не конфликтует с чужими.</p>
<h3>Где применяют UUID</h3>
<p>Идентификаторы нужны всюду, где объекты создаются независимо друг от друга: первичные ключи в распределённых базах, имена временных файлов, номера сессий, заказов и платежей, метки в логах. UUID удобен ещё и тем, что не выдаёт порядок создания и количество записей — в отличие от последовательных номеров.</p>
<h3>Почему здесь только версия 4</h3>
<p>У стандарта семь версий. V1 и v6 строятся от MAC-адреса и времени, v7 — от метки времени: они сортируются и дружелюбны к индексам, но раскрывают, когда и где созданы. V4 — чистая случайность: ничего не раскрывает и не требует исходных данных. Для большинства задач, от ключей в базе до имён файлов, это самый простой выбор.</p>
<p>Есть и обратная сторона: случайные UUID плохо сортируются, и вставка их в индекс базы данных идёт медленнее, чем у последовательных ключей. Если таблица огромная и запись в неё непрерывная, посмотрите в сторону UUID v7. Для обычных проектов разница незаметна.</p>
<p>Отдельно стоят версии v3, v5 и v8: они не случайны, а строятся хешированием имени внутри пространства имён — одинаковый вход всегда даёт одинаковый UUID. Это удобно, когда идентификатор нужно воспроизводить по исходным данным. Для свежих уникальных ключей, которые никому не должны быть предсказуемы, берут v4 или v7.</p>
<h3>Как пользоваться генератором</h3>
<p>Инструмент пригодится разработчику, тестировщику и аналитику: заполнить тестовую базу, разметить выгрузку, назначить идентификаторы черновикам. Порядок такой:</p>
<ul>
<li>Укажите количество — от одного идентификатора до целой пачки.</li>
<li>Кнопка «Ещё» заменяет текущую порцию новой, «Скопировать все» отправляет список в буфер обмена.</li>
<li>Сохраняйте нужные UUID сразу: генератор не хранит историю, после обновления страницы они исчезнут.</li>
</ul>""",
  "faq": [
    ("Чем UUID v4 отличается от v7?",
     "V4 — чистая случайность. V7 кодирует в начало метку времени, поэтому идентификаторы сортируются по времени создания и дружелюбнее к индексам баз данных. Здесь генерируется только v4."),
    ("Насколько надёжна генерация?",
     "Используется crypto.getRandomValues — тот же генератор, что браузер применяет для ключей шифрования. Math.random не используется вовсе."),
    ("Могут ли два сгенерированных UUID совпасть?",
     "Теоретически да, практически — нет: при миллиарде UUID в секунду столетие генерации даст шанс одной коллизии порядка 50%. Для любых прикладных задач риском пренебрегают."),
    ("Что делает кнопка «Ещё»?",
     "Генерирует новую порцию идентификаторов взамен текущей — в том же количестве, что указано в поле."),
    ("Что означает запись 8-4-4-4-12?",
     "Это 32 шестнадцатеричные цифры, разбитые дефисами на группы из 8, 4, 4, 4 и 12 символов. Цифра 4 в начале третьей группы — метка версии, первый символ четвёртой группы — метка варианта."),
    ("Можно ли использовать UUID как секретный токен?",
     "У UUID v4 — 122 бита энтропии, что достаточно для многих задач. Но для токенов доступа и ссылок сброса пароля лучше брать специально сгенерированные секреты: стандарт не считает UUID секретом."),
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
