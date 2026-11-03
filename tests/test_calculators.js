'use strict';
// Page-specific regression gate; no browser/packages/network required.
// Usage: node tests/test_calculators.js [site-root]
// Live Chrome QA remains mandatory: this focused DOM harness is not a rendering test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { webcrypto } = require('node:crypto');
const root = path.resolve(process.argv[2] || path.join(__dirname, '..'));
let checks = 0;
function check(condition, label){ assert.ok(condition, label); checks++; }

function load(route, marker){
  const html = fs.readFileSync(path.join(root, route, 'index.html'), 'utf8');
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  const nodes = new Map();
  const domReady = [];
  const makeNode = id => ({
    id, value: '', textContent: '', checked: false, disabled: false,
    min: '', max: '', style: {}, dataset: {}, listeners: [], attrs: {}, classes: new Set(),
    get valueAsNumber(){ return this.value.trim() === '' ? NaN : Number(this.value); },
    addEventListener(type, fn, capture = false){ this.listeners.push({ type, fn, capture }); },
    dispatch(type){
      for (const entry of this.listeners.filter(e => e.type === type).sort((a,b) => Number(b.capture) - Number(a.capture))) entry.fn.call(this, { target: this });
      if (type === 'input' && this.form) this.form.dispatch(type);
    },
    setAttribute(key, value){ this.attrs[key] = String(value); },
    querySelector(){ return getNode(this.id + '-span'); },
    closest(selector){ return getNode(selector); },
    get classList(){
      const classes = this.classes;
      return { remove: name => classes.delete(name), toggle: (name, active) => active ? classes.add(name) : classes.delete(name) };
    }
  });
  function getNode(id){ if (!nodes.has(id)) nodes.set(id, makeNode(id)); return nodes.get(id); }
  for (const tag of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)){
    const node = getNode(tag[1]);
    for (const attr of ['value', 'min', 'max']){
      const match = tag[0].match(new RegExp('\\b' + attr + '="([^"]*)"'));
      if (match) node[attr] = match[1];
    }
    node.checked = /\bchecked\b/.test(tag[0]);
  }
  const fields = ['of', 'of', 'share', 'share', 'change', 'change'].map((mode,i) => {
    const node = getNode('mode-field-' + i); node.dataset.mode = mode; return node;
  });
  for (const id of ['p-percent','p-number','p-part','p-whole','p-old','p-new']) getNode(id).form = getNode('percent-form');
  getNode('p-mode').value = 'of';
  const context = vm.createContext({
    document: { getElementById: getNode, querySelectorAll: () => fields,
      addEventListener: (type, fn) => { if (type === 'DOMContentLoaded') domReady.push(fn); } },
    window: {}, crypto: webcrypto, Uint32Array,
    formatMoney: value => Number(value).toFixed(0), formatMoney2: value => Number(value).toFixed(2),
    attachThousandsInput: el => {
      const format = () => { el.value = el.value.replace(/\D/g, ''); };
      format(); el.addEventListener('input', format);
    },
    console
  });
  function run(code){ return new vm.Script(code).runInContext(context, { timeout: 1500 }); }
  const formula = scripts.find(s => s.includes('const Calc ='));
  if (formula){
    run(formula);
    run('globalThis.calcCalls = 0; const originalLoan = Calc.annuityLoan; Calc.annuityLoan = function(...args){ calcCalls++; return originalLoan.apply(this, args); };');
  }
  const page = scripts.find(s => s.includes(marker));
  assert.ok(page, route + ': calculator script must exist');
  run(page);
  for (const callback of domReady){ context.__callback = callback; run('__callback()'); }
  function set(id, value, event = 'input'){
    getNode(id).value = String(value);
    context.__id = id; context.__event = event;
    run('document.getElementById(__id).dispatch(__event)');
  }
  return { nodes, getNode, context, run, set };
}

for (const [route,prefix,term,marker] of [
  ['kredit','c','c-months',"const amountEl = document.getElementById('c-amount')"],
  ['ipoteka','m','m-years',"const amountEl = document.getElementById('m-amount')"]
]){
  const page = load(route, marker);
  const result = page.getNode(prefix + '-payment');
  const invalid = label => {
    check(result.textContent === '—', label + ': cleared result');
    check(page.getNode('copy-btn').disabled && page.getNode('share-btn').disabled, label + ': disabled actions');
    check(page.getNode('.chart-wrap').style.display === 'none' && page.getNode('.schedule-block').style.display === 'none', label + ': chart/schedule hidden');
  };
  check(result.textContent !== '—', route + ': default valid');
  for (const value of ['', 0, -1, 1.5, 601, 1e308, Infinity, NaN, Number(page.getNode(term).max) + 1]){
    const calls = page.context.calcCalls;
    page.set(term, value); invalid(route + ': term ' + value);
    check(page.context.calcCalls === calls, route + ': invalid term rejected before Calc');
  }
  page.set(term, page.getNode(term).max);
  check(result.textContent !== '—' && !page.getNode('copy-btn').disabled, route + ': max term recovery');
  page.set(prefix + '-rate', 0);
  check(result.textContent !== '—', route + ': zero rate valid');
  check(Number(page.getNode(prefix + '-overpay').textContent.replace(/[^0-9.-]/g, '')) === 0, route + ': zero rate no overpayment');
  for (const value of ['', Infinity, NaN, -1, Number(page.getNode(prefix + '-rate').max) + 1]){
    const calls = page.context.calcCalls; page.set(prefix + '-rate', value); invalid(route + ': rate ' + value);
    check(page.context.calcCalls === calls, route + ': invalid rate rejected before Calc');
  }
  page.set(prefix + '-rate', 12);
  for (const value of ['', 'Infinity', '1e309', '-5', '12.5', '9007199254740992', '9'.repeat(400)]){
    const calls = page.context.calcCalls; page.set(prefix + '-amount', value); invalid(route + ': amount ' + value.slice(0,20));
    check(page.context.calcCalls === calls, route + ': invalid money rejected before Calc');
  }
  page.set(prefix + '-amount', 120000);
  check(result.textContent !== '—' && !page.getNode('share-btn').disabled, route + ': valid money recovery');
  if (route === 'ipoteka'){
    page.set('m-down', ''); check(result.textContent !== '—', 'ipoteka: optional empty down accepted');
    for (const down of ['x','-10','9007199254740992','120000']){ page.set('m-down', down); invalid('ipoteka: down ' + down); }
    page.set('m-down', 0); check(result.textContent !== '—', 'ipoteka: down recovery');
  }
}

{
  const page = load('procenty', "const modeEl = document.getElementById('p-mode')");
  const result = page.getNode('p-result');
  page.set('p-percent', 0); check(Number(result.textContent) === 0, 'percent: zero percentage valid');
  for (const mode of ['of','share','change']){
    page.set('p-mode', mode, 'change');
    const id = { of:'p-number', share:'p-whole', change:'p-old' }[mode];
    for (const value of ['', Infinity, NaN]){
      page.set(id, value);
      check(result.textContent === '—' && page.getNode('copy-btn').disabled && page.getNode('share-btn').disabled, 'percent: invalid ' + mode + ':' + value);
    }
    page.set(id, 100); check(result.textContent !== '—' && !page.getNode('copy-btn').disabled, 'percent: recovery ' + mode);
    if (mode !== 'of'){ page.set(id, 0); check(result.textContent === '—', 'percent: denominator zero ' + mode); page.set(id,100); }
  }
  page.set('p-mode','of','change'); page.set('p-percent',1e308); page.set('p-number',1e308);
  check(result.textContent === '—', 'percent: overflowing result invalid');
  page.set('p-percent',15); page.set('p-number',2000); check(Number(result.textContent) === 300, 'percent: normal recovery');
}

{
  const page = load('sluchaynye-chisla', 'const RANDOM_RANGE_LIMIT');
  function values(){ return page.getNode('r-result').textContent.split(', ').map(Number); }
  for (const [id,value] of [['max-val','4294967297'],['count','10001'],['min-val','9007199254740992'],['max-val','1e100'],['count','1.5'],['min-val','']]){
    page.set('min-val',0); page.set('max-val',100); page.set('count',1);
    page.set(id,value);
    check(page.getNode('r-result').textContent === '—' && page.getNode('copy-btn').disabled, 'random: rejected ' + id + '=' + value);
  }
  page.set('min-val',0); page.set('max-val',4294967295); page.set('count',10000);
  page.getNode('no-repeat').checked = true; page.run('generateNumbers()');
  let result = values();
  check(result.length === 10000 && new Set(result).size === 10000, 'random: huge range sparse unique 10000');
  check(result.every(n => Number.isSafeInteger(n) && n >= 0 && n <= 4294967295), 'random: endpoints bounded');
  page.set('count',100); page.set('min-val',-50); page.set('max-val',49);
  result = values(); check(result.length === 100 && new Set(result).size === 100 && Math.min(...result) === -50 && Math.max(...result) === 49, 'random: complete negative interval');
  page.set('count',101); check(page.getNode('r-result').textContent === '—', 'random: uniqueness exceeds range');
  page.context.crypto = { getRandomValues: a => { a[0] = 4294967295; return a; } };
  page.set('count',1); page.set('min-val',0); page.set('max-val',2);
  check(page.getNode('r-result').textContent === '—', 'random: broken entropy rejection bounded');
  for (const expression of ['secureInt(0)','secureInt(Infinity)','secureInt(4294967297)','randomInt(0,9007199254740992)']){
    assert.throws(() => page.run(expression)); checks++;
  }
}

{
  const page = load('generator-paroley', 'function generatePassword(');
  let copied = '';
  page.context.window.copyText = text => { copied = text; };
  page.getNode('r-password').textContent = 'FAKE-only-Test42';
  page.run("document.getElementById('copy-btn').dispatch('click')");
  check(copied === 'FAKE-only-Test42', 'password: delegates to common catch/fallback helper');
  copied = ''; page.getNode('r-password').textContent = '—';
  page.run("document.getElementById('copy-btn').dispatch('click')");
  check(copied === '', 'password: invalid result not copied');
}
console.log('PASS calculator regressions: ' + checks + ' assertions across 5 pages (' + root + ')');
