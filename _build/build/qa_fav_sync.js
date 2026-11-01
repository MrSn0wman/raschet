// qa_fav_sync.js — крестик в панели с НАСТОЯЩЕЙ страницы калькулятора:
// звезда в action-bar должна погаснуть, тост — показаться, панель — остаться открытой.
const { spawn } = require('child_process');
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const ch = spawn(CHROME, ['--headless=new', '--disable-gpu', '--remote-debugging-port=0',
    '--user-data-dir=' + require('os').tmpdir() + '\\cdpfav-' + Date.now(), 'about:blank'],
    { stdio: ['ignore', 'ignore', 'pipe'] });
  let err = '';
  const wsUrl = await new Promise((res, rej) => {
    ch.stderr.on('data', (d) => { err += d; const m = err.match(/DevTools listening on (ws:\/\/\S+)/); if (m) res(m[1]); });
    setTimeout(() => rej(new Error('timeout')), 20000);
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
  const seed = 'try{localStorage.setItem("raschet-theme","dark");localStorage.setItem("raschet-favs",JSON.stringify([{slug:"chaevye",title:"Чаевые",href:"/chaevye/"}]))}catch(e){}';
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', { source: seed });
  await send('Page.navigate', { url: 'http://127.0.0.1:8765/chaevye/' });
  await sleep(2500);
  const ev = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result.value;

  console.log('BADGE_BEFORE:', JSON.stringify(await ev('document.getElementById("fav-badge").textContent')));
  console.log('TOGGLE_BEFORE:', JSON.stringify(await ev('(()=>{const t=document.getElementById("fav-toggle");return t?{cls:t.className,label:t.querySelector("span").textContent,aria:t.getAttribute("aria-pressed")}:null})()')));
  await ev('document.getElementById("fav-btn").click()');
  await sleep(200);
  await ev('document.querySelector("#fav-list .fav-remove").click()');
  await sleep(300);
  console.log('TOGGLE_AFTER:', JSON.stringify(await ev('(()=>{const t=document.getElementById("fav-toggle");return t?{cls:t.className,label:t.querySelector("span").textContent,aria:t.getAttribute("aria-pressed")}:null})()')));
  console.log('TOAST:', JSON.stringify(await ev('(()=>{const t=document.querySelector(".toast");return t?{text:t.textContent,shown:t.classList.contains("show")}:null})()')));
  console.log('PANEL_OPEN:', JSON.stringify(await ev('!document.getElementById("fav-panel").hidden')));
  console.log('STORED:', JSON.stringify(await ev('localStorage.getItem("raschet-favs")')));
  console.log('CONSOLE_ERRORS:', JSON.stringify(errors));
  ws.close(); ch.kill();
})().then(() => process.exit(0), (e) => { console.error('FAIL:', e.message); process.exit(1); });