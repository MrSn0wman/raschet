// cdp_shot.js — скриншоты и замеры страниц в настоящем мобильном viewport через CDP.
// Chrome на Windows не даёт окно уже 500px, поэтому --window-size=320 не работает:
// здесь ширина задаётся через Emulation.setDeviceMetricsOverride.
//
// Запуск (node >= 22, встроенный WebSocket):
//   node cdp_shot.js --url http://127.0.0.1:8095/ --width 320 --height 1200 --shot out.png
//   node cdp_shot.js --url ... --theme dark --shot out.png
//   node cdp_shot.js --url ... --eval "document.documentElement.scrollWidth"   (печатает EVAL: ...)
//
// Chrome убить за собой: процесс завершается после снятия.
const { spawn } = require('child_process');
const fs = require('fs');

const args = {};
for (let i = 2; i < process.argv.length - 1; i += 2) {
  args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
}
const URL_ = args.url;
const WIDTH = parseInt(args.width || '320', 10);
const HEIGHT = parseInt(args.height || '1200', 10);
const SHOT = args.shot || null;
const THEME = args.theme || null;          // 'dark' | 'light' — seed localStorage до загрузки
const EVAL = args.eval || null;
const WAIT_MS = parseInt(args.wait || '1500', 10);
const CHROME = args.chrome || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

if (!URL_) { console.error('нужен --url'); process.exit(2); }

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--remote-debugging-port=0',
    '--user-data-dir=' + require('os').tmpdir() + '\\cdp-shot-' + Date.now(),
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

  // WS браузера → находим page target
  const port = new URL(wsUrl).port;
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  let page = targets.find(t => t.type === 'page');
  if (!page) {
    page = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  }

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let idSeq = 1;
  const pending = new Map();
  const events = [];
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    else if (msg.method) events.push(msg.method);
  });
  await new Promise((resolve) => ws.addEventListener('open', resolve));
  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = idSeq++;
      pending.set(id, (msg) => msg.error ? reject(new Error(method + ': ' + JSON.stringify(msg.error))) : resolve(msg.result));
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1, mobile: WIDTH < 500 });
  await send('Page.enable');
  if (THEME) {
    await send('Page.addScriptToEvaluateOnNewDocument', {
      source: `try{localStorage.setItem('raschet-theme','${THEME}')}catch(e){}`,
    });
  }
  await send('Page.navigate', { url: URL_ });
  // ждём load + доп. время на SW/шрифты/fetch
  const t0 = Date.now();
  while (!events.includes('Page.loadEventFired') && Date.now() - t0 < 15000) await sleep(100);
  await sleep(WAIT_MS);

  if (EVAL) {
    const r = await send('Runtime.evaluate', { expression: EVAL, returnByValue: true, awaitPromise: true });
    console.log('EVAL:', JSON.stringify(r.result && r.result.value));
  }
  if (SHOT) {
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(SHOT, Buffer.from(shot.data, 'base64'));
    console.log('SHOT:', SHOT);
  }

  ws.close();
  chrome.kill();
  // дождаться выхода, чтобы не оставлять процессы
  await new Promise(r => chrome.on('exit', r));
}

main().then(() => process.exit(0), (e) => { console.error('FAIL:', e.message); process.exit(1); });
