# -*- coding: utf-8 -*-
# Счётчик слов и символов: живые счётчики по мере ввода.

TOOL = {
  "slug": "schetchik-slov",
  "title": "Счётчик слов и символов",
  "meta_title": "Счётчик слов и символов онлайн — время чтения",
  "meta_desc": "Посчитайте слова, символы с пробелами и без, предложения и абзацы в тексте. Оценка времени чтения из расчёта 200 слов в минуту.",
  "h1": "Счётчик слов и символов",
  "sub": "Сколько слов, символов и минут чтения в вашем тексте — счётчики обновляются по мере ввода.",
  "category": "Текст",
  "fields_html": """
<div class="field-grid">
  <div class="field full">
    <label for="wc-text">Текст</label>
    <textarea id="wc-text" rows="9" placeholder="Вставьте статью, пост или письмо — всё посчитается автоматически"></textarea>
  </div>
</div>
""",
  "result_html": """
<div class="result-panel">
  <div class="r-label">Слов в тексте</div>
  <div class="r-value" id="wc-words">0</div>
  <div class="r-rows">
    <div><b id="wc-chars">0</b><span>символов с пробелами</span></div>
    <div><b id="wc-nospace">0</b><span>символов без пробелов</span></div>
    <div><b id="wc-sent">0</b><span>предложений</span></div>
    <div><b id="wc-para">0</b><span>абзацев (непустых строк)</span></div>
    <div><b id="wc-time">—</b><span>время чтения (~200 слов/мин)</span></div>
  </div>
</div>
""",
  "explain_html": """<h2>Как это работает</h2>
<p>Счётчики обновляются при каждом изменении текста — отдельная кнопка не нужна. Словом считается любой фрагмент между пробелами, в котором есть хотя бы одна буква или цифра: «неужели», «v2.0» и «123» — слова, а одиночный дефис или тире — нет. Такой подсчёт совпадает с Word и Google Docs в подавляющем большинстве случаев.</p>
<p>Предложения определяются по знакам конца фразы — точке, восклицательному и вопросительному знакам, многоточию. Абзац — любая непустая строка, поэтому маркированный список из пяти строк даст пять абзацев. Это стоит учитывать при подготовке текстов с жёсткими требованиями к объёму.</p>
<p>Время чтения оценивается из средней скорости взрослого читателя — около 200 слов в минуту для русского текста. Это ориентир для черновой оценки: технический текст читают медленнее, художественный — быстрее.</p>""",
  "faq": [
    ("Почему счётчик слов отличается от Word?",
     "Word и наш счётчик по-разному трактуют редкие случаи: слова через дефис, сноски, отдельно стоящие знаки препинания. Для обычного текста расхождение не больше 1–2 слов на тысячу."),
    ("Что считается абзацем?",
     "Любая непустая строка. Если текст разбит пустыми строками, каждый блок — абзац; если каждая строка списка идёт с новой строки, каждая из них тоже считается абзацем."),
    ("Как посчитать время озвучки текста, а не чтения?",
     "Для дикторской озвучки берите 100–120 слов в минуту: разделите число слов на 110 — получите примерную длительность в минутах."),
    ("Есть ли ограничение на размер текста?",
     "Нет, подсчёт выполняется локально в браузере и мгновенно справляется с текстами в сотни тысяч символов."),
  ],
  "page_js": r"""
(function(){
  'use strict';

  var textEl = document.getElementById('wc-text');
  var wordsEl = document.getElementById('wc-words');
  var charsEl = document.getElementById('wc-chars');
  var nospaceEl = document.getElementById('wc-nospace');
  var sentEl = document.getElementById('wc-sent');
  var paraEl = document.getElementById('wc-para');
  var timeEl = document.getElementById('wc-time');

  function plural(n, one, few, many){
    var m = Math.abs(n) % 100;
    var d = m % 10;
    if (m > 10 && m < 20) return many;
    if (d > 1 && d < 5) return few;
    if (d === 1) return one;
    return many;
  }

  function render(){
    var text = textEl.value;
    var chars = text.length;
    var nospace = text.replace(/\s/g, '').length;

    var words = 0;
    var tokens = text.split(/\s+/);
    for (var i = 0; i < tokens.length; i++){
      if (/[0-9A-Za-zА-Яа-яЁё]/.test(tokens[i])) words++;
    }

    var sentences = 0;
    var sm = text.match(/[^.!?…]+[.!?…]+/g);
    if (sm) sentences = sm.length;
    else if (words > 0) sentences = 1;

    var paragraphs = 0;
    var lines = text.split('\n');
    for (var j = 0; j < lines.length; j++){
      if (lines[j].trim() !== '') paragraphs++;
    }

    var timeText;
    if (words === 0){
      timeText = '—';
    } else if (words < 200){
      timeText = 'меньше минуты';
    } else {
      var rm = Math.max(1, Math.round(words / 200));
      timeText = rm + ' ' + plural(rm, 'минута', 'минуты', 'минут');
    }

    wordsEl.textContent = window.formatMoney(words);
    charsEl.textContent = window.formatMoney(chars);
    nospaceEl.textContent = window.formatMoney(nospace);
    sentEl.textContent = window.formatMoney(sentences);
    paraEl.textContent = window.formatMoney(paragraphs);
    timeEl.textContent = timeText;
  }

  textEl.addEventListener('input', render);
  render();
})();
""",
  "page_css": "",
  "related": ["transliteraciya", "udalenie-dubley-strok", "lorem-ipsum", "summa-propisyu"],
}
