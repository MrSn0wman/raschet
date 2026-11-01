// qa_fav_remove.js — проверка крестика в панели «Избранное» (удаление без перехода в калькулятор).
// Запуск: node qa_fav_remove.js --url http://127.0.0.1:8765/ --width 1280 --shot out.png
const { spawn } = require('child_process');
const fs = require('fs');

const args = {};
for (let i = 2; i < process.argv.length - 1; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const URL_ = args.url;
const WIDTH = parseInt(args.width || '1280', 10);
const HEIGHT = parseInt(args.height || '800', 10);
const SHOT = args.shot || null;
const THEME = args.theme || null;
const CHROME = args.chrome || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--remote-debugging-port=0', '--user-data-dir=' + require('os').tmpdir() + '\\cdp-fav-' + Date.now(), 'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  let err = '';
  const wsUrl = await new Promise((resolve, reject) => {
    chrome.stderr.on('data', (d) => { err += d; const m = err.match(/DevTools listening on (ws:\/\/\S+)/); if (m) resolve(m[1]); });
    setTimeout(() => reject(new Error('timeout DevTools')), 20000);
  });
  const port = new URL(wsUrl).port;
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page = targets.find((t) => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let idSeq = 1; const pending = new Map(); const logs = []; const errors = [];
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); return; }
    if (msg.method === 'Runtime.consoleAPICalled') logs.push(msg.params.type + ': ' + msg.params.args.map((a) => a.value ?? a.description).join(' '));
    if (msg.method === 'Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.text + ' ' + (msg.params.exceptionDetails.exception?.description || ''));
  });
  await new Promise((r) => ws.addEventListener('open', r));
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = idSeq++;
    pending.set(id, (m) => (m.error ? reject(new Error(method + ': ' + JSON.stringify(m.error))) : resolve(m.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });

  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1, mobile: WIDTH < 500 });
  await send('Page.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', {
    source: `try{
      localStorage.setItem('raschet-theme','${THEME || 'dark'}');
      localStorage.setItem('raschet-favs', JSON.stringify([
        {slug:'slozhnyy-procent', title:'Сложный процент', href:'../slozhnyy-procent/'},
        {slug:'chaevye', title:'Чаевые', href:'../chaevye/'}
      ]));
    }catch(e){}`,
  });
  await send('Page.navigate', { url: URL_ });
  await sleep(2000);

  const ev = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result.value;

  // открыть панель
  const opened = await ev(`(() => {
    const b = document.getElementById('fav-btn'), p = document.getElementById('fav-panel');
    if (!b || !p) return 'no-panel';
    b.click();
    return { hidden: p.hidden, rows: document.querySelectorAll('#fav-list .fav-row').length,
             removes: document.querySelectorAll('#fav-list .fav-remove').length,
             badge: document.getElementById('fav-badge').textContent };
  })()`);
  console.log('OPEN:', JSON.stringify(opened));
  if (SHOT) {
    const s = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(SHOT, Buffer.from(s.data, 'base64'));
    console.log('SHOT:', SHOT);
  }

  // клик по крестику первого элемента
  const afterRemove = await ev(`(() => {
    const before = location.href;
    const rm = document.querySelector('#fav-list .fav-remove');
    if (!rm) return 'no-remove-button';
    rm.click();
    const p = document.getElementById('fav-panel');
    return {
      navigated: location.href !== before,
      rows: document.querySelectorAll('#fav-list .fav-row').length,
      titles: [...document.querySelectorAll('#fav-list .fav-row a')].map(a => a.textContent),
      badge: document.getElementById('fav-badge').textContent,
      badgeHidden: document.getElementById('fav-badge').hidden,
      panelHidden: p.hidden,
      stored: JSON.parse(localStorage.getItem('raschet-favs') || '[]').map(i => i.slug),
      toast: (document.getElementById('toast') || {}).textContent || null,
      focusClass: document.activeElement && document.activeElement.className
    };
  })()`);
  console.log('AFTER_REMOVE:', JSON.stringify(afterRemove));

  // удалить последний — пустое состояние
  const emptied = await ev(`(() => {
    const rm = document.querySelector('#fav-list .fav-remove');
    if (rm) rm.click();
    return {
      rows: document.querySelectorAll('#fav-list .fav-row').length,
      emptyShown: !document.getElementById('fav-empty').hidden,
      badgeHidden: document.getElementById('fav-badge').hidden,
      stored: JSON.parse(localStorage.getItem('raschet-favs') || '[]').length,
      panelHidden: document.getElementById('fav-panel').hidden
    };
  })()`);
  console.log('EMPTIED:', JSON.stringify(emptied));

  // перезагрузка: состояние не откатилось
  await send('Page.navigate', { url: URL_ });
  await sleep(1500);
  console.log('RELOAD_BADGE:', JSON.stringify(await ev(`(() => ({ hidden: document.getElementById('fav-badge').hidden, stored: JSON.parse(localStorage.getItem('raschet-favs')||'[]').length }))()`)));

  console.log('CONSOLE_ERRORS:', JSON.stringify(errors));
  ws.close(); chrome.kill();
  await new Promise((r) => chrome.on('exit', r));
}
main().then(() => process.exit(0), (e) => { console.error('FAIL:', e.message); process.exit(1); });