# -*- coding: utf-8 -*-
# Сборка calc-mortgage.html v2 из канонических частей + контента/логики старой страницы.
import json
import re
import io
import os

SRC = r"C:\Kimi\raschet\calc-mortgage.html"
PARTS = r"C:\Kimi\raschet-redesign\parts"
OUT = r"C:\Kimi\raschet-redesign\calc-mortgage.html"
BASE_URL = "https://raschet.net/"

def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

style_css = read(os.path.join(PARTS, "style.css"))
fonts_css = read(os.path.join(PARTS, "fonts.css")).replace("__PREFIX__", "")
style_css = fonts_css + "\n" + style_css
header = read(os.path.join(PARTS, "header.html"))
footer = read(os.path.join(PARTS, "footer.html"))
head_init = read(os.path.join(PARTS, "head-init.html"))
ui_js = read(os.path.join(PARTS, "ui.js"))

old = read(SRC)

def must(pattern, text, flags=0, name=""):
    m = re.search(pattern, text, flags)
    if not m:
        raise SystemExit("NOT FOUND: " + name)
    return m

# --- мета ---
title = must(r"<title>(.*?)</title>", old, re.S, "title").group(1).strip()
desc = must(r'<meta name="description" content="([^"]*)"', old, 0, "description").group(1)
og_title_m = re.search(r'<meta property="og:title" content="([^"]*)"', old)
og_desc_m = re.search(r'<meta property="og:description" content="([^"]*)"', old)
og_title = og_title_m.group(1) if og_title_m else title
og_desc = og_desc_m.group(1) if og_desc_m else desc

# --- JSON-LD (два блока) ---
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', old, re.S)
assert len(ld_blocks) == 2, "json-ld blocks: %d" % len(ld_blocks)
ld_out = []
for raw in ld_blocks:
    obj = json.loads(raw)
    def fix(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, str) and "raschet.rf" in v:
                    node[k] = v.replace("https://raschet.rf/", BASE_URL)
                else:
                    fix(v)
        elif isinstance(node, list):
            for item in node:
                fix(item)
    fix(obj)
    ld_out.append(json.dumps(obj, ensure_ascii=False, indent=2))

# --- куски тела из старой страницы ---
breadcrumbs = must(r'<p class="breadcrumbs">.*?</p>', old, re.S, "breadcrumbs").group(0)
form = must(r'<form id="mortgage-form".*?</form>', old, re.S, "form").group(0)
result_panel = must(r'<div class="result-panel">.*?</div>\s*</div>', old, re.S, "result-panel")
# result-panel внутри calc-card: берём точно блок от <div class="result-panel"> до его закрытия по балансу скобок нельзя — используем известный хвост
rp = must(r'<div class="result-panel">.*?</div>\s*</div>\s*</div>', old, re.S, "result-panel2")
article = must(r'<article class="calc-explain">.*?</article>', old, re.S, "article").group(0)
aside = must(r'<aside class="sidebar">.*?</aside>', old, re.S, "aside").group(0)

# result-panel: аккуратно извлечём простым счётчиком вложенности div
def extract_balanced(text, start_marker):
    i = text.find(start_marker)
    assert i >= 0, start_marker
    depth = 0
    j = i
    while True:
        nxt_open = text.find("<div", j)
        nxt_close = text.find("</div>", j)
        if nxt_close < 0:
            raise SystemExit("unbalanced: " + start_marker)
        if 0 <= nxt_open < nxt_close:
            depth += 1
            j = nxt_open + 4
        else:
            depth -= 1
            j = nxt_close + 6
            if depth == 0:
                return text[i:j]

result_panel = extract_balanced(old, '<div class="result-panel">')

# --- правки формы: data-share, inputmode, role=alert ---
form = form.replace('<input type="text" id="m-amount" value="5000000" required>',
                    '<input type="text" id="m-amount" value="5000000" required inputmode="numeric" data-share="amount">')
form = form.replace('<input type="number" id="m-rate" value="12" min="0" max="50" step="0.1" required>',
                    '<input type="number" id="m-rate" value="12" min="0" max="50" step="0.1" required data-share="rate">')
form = form.replace('<input type="number" id="m-years" value="20" min="1" max="30" step="1" required>',
                    '<input type="number" id="m-years" value="20" min="1" max="30" step="1" required data-share="years">')
form = form.replace('<input type="text" id="m-down" value="0">',
                    '<input type="text" id="m-down" value="0" inputmode="numeric" data-share="down">')
form = form.replace('<div class="error-msg" id="m-error">', '<div class="error-msg" id="m-error" role="alert">')
assert 'data-share="amount"' in form and 'data-share="down"' in form

# --- библиотека Calc: блок <script>, содержащий annuityLoan, без src ---
scripts = re.findall(r"<script>(.*?)</script>", old, re.S)
calc_lib = None
for s in scripts:
    if "annuityLoan" in s and "window.Calc" in s or (s and "annuityLoan" in s and "Calc" in s):
        calc_lib = s
        break
if calc_lib is None:
    # fallback: любой скрипт с annuityLoan
    for s in scripts:
        if "annuityLoan" in s:
            calc_lib = s
            break
assert calc_lib, "Calc lib not found"

# --- новые блоки v2 ---
ACTION_BAR = """
          <div class="action-bar">
            <button class="action-btn" id="fav-toggle" type="button" aria-pressed="false"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3.6l2.5 5.2 5.7.7-4.2 3.9 1.1 5.6-5.1-2.8-5.1 2.8 1.1-5.6L3.8 9.5l5.7-.7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg><span>В избранное</span></button>
            <button class="action-btn" id="share-btn" type="button"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="18" cy="5" r="2.6" stroke="currentColor" stroke-width="1.6"/><circle cx="6" cy="12" r="2.6" stroke="currentColor" stroke-width="1.6"/><circle cx="18" cy="19" r="2.6" stroke="currentColor" stroke-width="1.6"/><path d="M8.2 10.6l7.6-4.4M8.2 13.4l7.6 4.4" stroke="currentColor" stroke-width="1.6"/></svg><span>Поделиться</span></button>
            <button class="action-btn" id="copy-btn" type="button" data-copy-target="#m-payment"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span>Копировать</span></button>
            <button class="action-btn" id="print-btn" type="button"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 8V3h10v5" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><rect x="3" y="8" width="18" height="9" rx="1.8" stroke="currentColor" stroke-width="1.6"/><path d="M7 13.5h10V21H7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg><span>Печать</span></button>
          </div>
"""

CHART = """
          <div class="chart-wrap">
            <svg id="m-chart" width="140" height="140" viewBox="0 0 42 42" role="img" aria-label="Соотношение тела кредита и переплаты">
              <circle cx="21" cy="21" r="15.9155" fill="none" stroke="var(--gold-soft)" stroke-width="6"></circle>
              <circle id="m-chart-a" cx="21" cy="21" r="15.9155" fill="none" stroke="var(--accent)" stroke-width="6" pathLength="100" stroke-dasharray="37.84 62.16" stroke-dashoffset="25"></circle>
              <circle id="m-chart-b" cx="21" cy="21" r="15.9155" fill="none" stroke="var(--gold)" stroke-width="6" pathLength="100" stroke-dasharray="62.16 37.84" stroke-dashoffset="-12.84"></circle>
            </svg>
            <div class="chart-legend">
              <div><span class="sw" style="background:var(--accent)"></span>Тело кредита — <b id="m-legend-principal">5 000 000 ₽</b></div>
              <div><span class="sw" style="background:var(--gold)"></span>Переплата — <b id="m-legend-overpay">8 213 034 ₽</b></div>
            </div>
          </div>
"""

SCHEDULE = """
          <div class="schedule-wrap">
            <table class="schedule-table">
              <thead><tr><th>Мес.</th><th>Платёж</th><th>Проценты</th><th>Тело</th><th>Остаток</th></tr></thead>
              <tbody id="m-schedule"></tbody>
            </table>
          </div>
          <button class="action-btn schedule-toggle" id="m-schedule-toggle" type="button"><span>Показать весь график</span></button>
"""

AD_PLACEHOLDER = """
          <div class="ad-slot ad-slot--inline" role="complementary" aria-label="Рекламный блок"><span class="tag">Реклама</span><span>Место для партнёрских предложений банков</span></div>
"""

# --- новая страничная логика ---
PAGE_JS = r"""
(function(){
  const amountEl = document.getElementById('m-amount');
  const rateEl = document.getElementById('m-rate');
  const yearsElRef = document.getElementById('m-years');
  const downEl = document.getElementById('m-down');
  const errorEl = document.getElementById('m-error');
  const tbody = document.getElementById('m-schedule');
  const toggleBtn = document.getElementById('m-schedule-toggle');
  let showAll = false;
  let schedule = [];

  attachThousandsInput(amountEl);
  attachThousandsInput(downEl);

  function renderChart(principal, totalInterest, totalPayment){
    const c1 = document.getElementById('m-chart-a');
    const c2 = document.getElementById('m-chart-b');
    if (!c1 || !c2 || !(totalPayment > 0)) return;
    const p = Math.max(0, Math.min(100, (principal / totalPayment) * 100));
    const o = 100 - p;
    c1.setAttribute('stroke-dasharray', p.toFixed(2) + ' ' + o.toFixed(2));
    c1.setAttribute('stroke-dashoffset', '25');
    c2.setAttribute('stroke-dasharray', o.toFixed(2) + ' ' + p.toFixed(2));
    c2.setAttribute('stroke-dashoffset', (25 - p).toFixed(2));
    document.getElementById('m-legend-principal').textContent = formatMoney(principal) + ' ₽';
    document.getElementById('m-legend-overpay').textContent = formatMoney(totalInterest) + ' ₽';
  }

  function buildSchedule(principal, rate, months, monthlyPayment){
    const rows = [];
    let balance = principal;
    const i = rate / 100 / 12;
    for (let m = 1; m <= months; m++){
      const interest = balance * i;
      let body = monthlyPayment - interest;
      if (body > balance) body = balance;
      balance = Math.max(0, balance - body);
      rows.push({ m: m, pay: interest + body, interest: interest, body: body, balance: balance });
      if (balance <= 0) break;
    }
    return rows;
  }

  function renderSchedule(){
    if (!tbody) return;
    const rows = showAll ? schedule : schedule.slice(0, 12);
    tbody.innerHTML = rows.map(function(r){
      return '<tr><td>' + r.m + '</td><td>' + formatMoney(r.pay) + ' ₽</td><td>' +
             formatMoney(r.interest) + ' ₽</td><td>' + formatMoney(r.body) + ' ₽</td><td>' +
             formatMoney(r.balance) + ' ₽</td></tr>';
    }).join('');
    if (toggleBtn){
      toggleBtn.style.display = schedule.length > 12 ? '' : 'none';
      toggleBtn.querySelector('span').textContent = showAll
        ? 'Свернуть график'
        : 'Показать весь график (' + schedule.length + ' мес.)';
    }
  }

  function render(){
    const amount = parseFormattedNumber(amountEl);
    const rate = parseFloat(rateEl.value);
    let years = parseFloat(yearsElRef.value);
    const down = parseFormattedNumber(downEl) || 0;

    const valid = amount > 0 && rate >= 0 && years > 0 && down >= 0 && down < amount;
    errorEl.classList.toggle('visible', !valid);
    if (!valid) return;

    // кламп срока: не больше 50 лет → максимум 600 итераций помесячного цикла
    years = Math.min(Math.max(years, 1), 50);

    const principal = amount - down;
    const months = Math.round(years * 12);
    const result = Calc.annuityLoan(principal, rate, months);

    document.getElementById('m-payment').textContent = formatMoney(result.monthlyPayment) + ' ₽';
    document.getElementById('m-total').textContent = formatMoney(result.totalPayment) + ' ₽';
    document.getElementById('m-overpay').textContent = formatMoney(result.totalInterest) + ' ₽';
    document.getElementById('m-principal').textContent = formatMoney(principal) + ' ₽';
    document.getElementById('m-months').textContent = months;

    renderChart(principal, result.totalInterest, result.totalPayment);
    schedule = buildSchedule(principal, rate, months, result.monthlyPayment);
    renderSchedule();
  }

  [amountEl, rateEl, yearsElRef, downEl].forEach(function(el){
    el.addEventListener('input', render);
  });
  if (toggleBtn){
    toggleBtn.addEventListener('click', function(){
      showAll = !showAll;
      renderSchedule();
    });
  }
  render();
})();
"""

# --- сборка main ---
main_html = """
  <div class="container">
    %s
    <div class="calc-layout">
      <div class="calc-main">
        <div class="calc-card">
          <h1>Калькулятор ипотеки</h1>
          <p class="calc-sub">Рассчитайте ежемесячный платёж, переплату и общую стоимость ипотеки по аннуитетной схеме — так же, как считает банк.</p>
          %s
          %s
          %s
          %s
          %s
          %s
        </div>
        %s
      </div>
      %s
    </div>
  </div>
""" % (breadcrumbs, form, ACTION_BAR, result_panel, CHART, SCHEDULE, AD_PLACEHOLDER, article, aside)

page = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%scalc-mortgage.html">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:url" content="%scalc-mortgage.html">
%s<style>
%s
</style>
<script type="application/ld+json">
%s
</script>
<script type="application/ld+json">
%s
</script>
</head>
<body data-calc-slug="mortgage" data-calc-title="Ипотека">
%s
<main id="main-content" class="calc-page">%s</main>
%s
<script>
%s
</script>
<script>
%s
</script>
<script>
%s
</script>
</body>
</html>
""" % (title, desc, BASE_URL, og_title, og_desc, BASE_URL,
       head_init, style_css, ld_out[0], ld_out[1], header, main_html, footer,
       ui_js, calc_lib, PAGE_JS)

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(page)

print("OK written:", OUT, len(page), "chars")
for token in ['data-calc-slug="mortgage"', 'id="mega-btn"', 'id="fav-toggle"', 'id="share-btn"',
              'id="copy-btn"', 'id="print-btn"', 'id="m-chart"', 'id="m-chart-a"', 'id="m-schedule"',
              'id="m-schedule-toggle"', 'data-share="amount"', 'data-share="rate"',
              'data-share="years"', 'data-share="down"', 'role="alert"', 'id="main-content"']:
    assert token in page, "missing " + token
for bad in ['raschet.rf', 'nav-drop', 'referral-block', 'onclick=', 'Северный', 'ФинТраст']:
    assert bad not in page, "forbidden token present: " + bad
print("self-checks: ALL PASS")
