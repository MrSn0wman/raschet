// qa_check.js — QA-прогон страницы через CDP: JS-ошибки, проверки DOM, скриншот.
// Запуск: node qa_check.js --url http://127.0.0.1:8323/ --width 1280 --height 1200 --shot out.png [--theme dark] [--wait 2000] [--checks '{"badge":true}']
// Печатает JSON-отчёт одной строкой: REPORT: {...}
const { spawn } = require('child_process');
const fs = require('fs');

const args = {};
for (let i = 2; i < process.argv.length - 1; i += 2) {
  args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
}
const URL_ = args.url;
const WIDTH = parseInt(args.width || '1280', 10);
const HEIGHT = parseInt(args.height || '1200', 10);
const SHOT = args.shot || null;
const THEME = args.theme || null;
const EVAL = args.eval || null;
const WAIT_MS = parseInt(args.wait || '1800', 10);
const CHROME = args.chrome || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

if (!URL_) { console.error('нужен --url'); process.exit(2); }
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function main() {
  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--remote-debugging-port=0',
    '--user-data-dir=' + require('os').tmpdir() + '\\qa-check-' + Date.now(),
    'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });

  let stderrBuf = '';
  const wsUrl = await new Promise((resolve, reject) => {
    chrome.stderr.on('data', (d) => {
      stderrBuf += d.toString();
      const m = stderrBuf.match(/DevTools listening on (ws:\/\/\S+)/);
      if (m) resolve(m[1]);
    });
    chrome.on('exit', () => reject(new Error('Chrome exited. stderr: ' + stderrBuf.slice(-500))));
    setTimeout(() => reject(new Error('timeout waiting DevTools. stderr: ' + stderrBuf.slice(-500))), 20000);
  });

  const port = new URL(wsUrl).port;
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  let page = targets.find(t => t.type === 'page');
  if (!page) page = await (await fetch(`http://127.0.0.1:${port}/json/new?about=blank`, { method: 'PUT' })).json();

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let idSeq = 1;
  const pending = new Map();
  const loadEvents = [];
  const jsErrors = [];   // Runtime.exceptionThrown
  const consoleErrors = []; // console.error(...)
  const netFailures = []; // Network.loadingFailed / bad statuses

  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); return; }
    if (msg.method === 'Page.loadEventFired') loadEvents.push(msg.method);
    if (msg.method === 'Runtime.exceptionThrown') {
      const d = msg.params.exceptionDetails;
      const txt = (d.exception && (d.exception.description || d.exception.value)) || d.text;
      jsErrors.push(txt);
    }
    if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
      consoleErrors.push(msg.params.args.map(a => a.value ?? a.description ?? '').join(' '));
    }
    if (msg.method === 'Network.loadingFailed') {
      netFailures.push('loadingFailed: ' + msg.params.errorText);
    }
    if (msg.method === 'Network.responseReceived') {
      const r = msg.params.response;
      if (r.status >= 400 && !r.url.includes('favicon')) netFailures.push(r.status + ' ' + r.url);
    }
  });
  await new Promise((resolve) => ws.addEventListener('open', resolve));
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = idSeq++;
    pending.set(id, (msg) => msg.error ? reject(new Error(method + ': ' + JSON.stringify(msg.error))) : resolve(msg.result));
    ws.send(JSON.stringify({ id, method, params }));
  });

  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1, mobile: WIDTH < 500 });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  if (THEME) {
    await send('Page.addScriptToEvaluateOnNewDocument', {
      source: `try{localStorage.setItem('raschet-theme','${THEME}')}catch(e){}`,
    });
  }
  await send('Page.navigate', { url: URL_ });
  const t0 = Date.now();
  while (!loadEvents.length && Date.now() - t0 < 15000) await sleep(100);
  await sleep(WAIT_MS);

  // Стандартные проверки рендера/брендинга
  const CHECKS = `(() => {
    const out = {};
    const html = document.documentElement;
    out.htmlClass = html.className || '';
    const header = document.querySelector('header') || document.body;
    const htext = (header ? header.innerText : document.body.innerText.slice(0, 2000)) || '';
    out.headerHasRaschet = /Расч[её]т/i.test(htext);
    out.headerHasNet = /\\.net/i.test(htext);
    out.headerHasRf = /\\.рф|\\.rf/i.test(htext);
    const canon = document.querySelector('link[rel="canonical"]');
    out.canonical = canon ? canon.href : null;
    out.canonicalOk = !!(canon && canon.href.startsWith('https://raschet.net/'));
    out.title = document.title;
    out.titleHasRf = /\\.рф/.test(document.title);
    out.bodyTextHasRf = /\\.рф|Расч[её]т\\.рф/i.test(document.body.innerText);
    const btns = document.querySelectorAll('button').length;
    out.buttonCount = btns;
    out.hasCanvas = !!document.querySelector('canvas');
    out.hasForm = !!document.querySelector('form');
    return out;
  })()`;
  let checks = {};
  try {
    const r = await send('Runtime.evaluate', { expression: CHECKS, returnByValue: true, awaitPromise: true });
    checks = r.result && r.result.value || {};
  } catch (e) { checks = { evalError: e.message }; }

  let extra = null;
  if (EVAL) {
    try {
      const r = await send('Runtime.evaluate', { expression: EVAL, returnByValue: true, awaitPromise: true });
      extra = r.result && r.result.value;
    } catch (e) { extra = { evalError: e.message }; }
  }

  if (SHOT) {
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(SHOT, Buffer.from(shot.data, 'base64'));
  }

  const report = {
    url: URL_, width: WIDTH, theme: THEME || 'default',
    jsErrors, consoleErrors, netFailures,
    checks, extra,
    shot: SHOT || null,
  };
  console.log('REPORT: ' + JSON.stringify(report, null, 1));

  ws.close();
  chrome.kill();
  await new Promise(r => chrome.on('exit', r));
}

main().then(() => process.exit(0), (e) => { console.error('FAIL:', e.message); process.exit(1); });
