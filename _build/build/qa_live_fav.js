// qa_live_fav.js — проверка крестика на ЖИВОМ сайте (после деплоя Pages).
const { spawn } = require('child_process');
const URL_ = process.argv[2] || 'https://raschet.net/';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const ch = spawn(CHROME, ['--headless=new', '--disable-gpu', '--remote-debugging-port=0',
    '--user-data-dir=' + require('os').tmpdir() + '\\live-' + Date.now(), 'about:blank'],
    { stdio: ['ignore', 'ignore', 'pipe'] });
  let err = '';
  const wsUrl = await new Promise((res, rej) => {
    ch.stderr.on('data', (d) => { err += d; const m = err.match(/DevTools listening on (ws:\/\/\S+)/); if (m) res(m[1]); });
    setTimeout(() => rej(new Error('timeout DevTools')), 20000);
  });
  const port = new URL(wsUrl).port;
  const targets = await (await fetch('http://127.0.0.1:' + port + '/json/list')).json();
  const page = targets.find((x) => x.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 1; const pend = new Map(); const errors = [];
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); return; }
    if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.text);
  });
  await new Promise((r) => ws.addEventListener('open', r));
  const send = (method, params = {}) => new Promise((res, rej) => {
    const i = id++; pend.set(i, (m) => (m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)));
    ws.send(JSON.stringify({ id: i, method, params }));
  });
  const ev = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result.value;

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.navigate', { url: URL_ });
  await sleep(4000);
  console.log('TITLE:', JSON.stringify(await ev('document.title')));
  const res = await ev(`(() => {
    localStorage.setItem('raschet-favs', JSON.stringify([
      {slug:'chaevye', title:'Чаевые', href:'/chaevye/'},
      {slug:'ipoteka', title:'Ипотека', href:'/ipoteka/'}
    ]));
    const b = document.getElementById('fav-btn');
    b.click();
    const rows = document.querySelectorAll('#fav-list .fav-row').length;
    const rem = document.querySelectorAll('#fav-list .fav-remove').length;
    document.querySelector('#fav-list .fav-remove').click();
    return {
      rowsBefore: rows, removesBefore: rem,
      rowsAfter: document.querySelectorAll('#fav-list .fav-row').length,
      stored: JSON.parse(localStorage.getItem('raschet-favs') || '[]').map(i => i.slug),
      badge: document.getElementById('fav-badge').textContent,
      panelOpen: !document.getElementById('fav-panel').hidden,
      cssApplied: getComputedStyle(document.querySelector('#fav-list .fav-row')).display
    };
  })()`);
  console.log('LIVE:', JSON.stringify(res));
  console.log('CONSOLE_ERRORS:', JSON.stringify(errors));
  ws.close(); ch.kill();
})().then(() => process.exit(0), (e) => { console.error('FAIL:', e.message); process.exit(1); });