// Portable all-page Chrome smoke harness. Built-in Node HTTP/WebSocket only.
// Python test_site owns the local http.server; this harness owns fresh Chrome.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const options = {};
for (let i=2;i<process.argv.length;i+=2) options[process.argv[i].replace(/^--/,'')] = process.argv[i+1];
const results = {complete:false,pages:[],errors:[]};
let chrome;
let profile;
const sockets = new Set();
async function connect(url){
  const ws = new WebSocket(url);
  sockets.add(ws);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  let sequence=0;
  const pending=new Map();
  const listeners=new Map();
  ws.addEventListener('message', event=>{
    const message=JSON.parse(event.data);
    if(message.id){
      const entry=pending.get(message.id);
      if(entry){clearTimeout(entry.timer);pending.delete(message.id);message.error?entry.reject(new Error(JSON.stringify(message.error))):entry.resolve(message.result);}
    } else for(const handler of listeners.get(message.method)||[]) handler(message.params);
  });
  return {close(){ws.close();sockets.delete(ws);},on(method,handler){listeners.set(method,[...(listeners.get(method)||[]),handler]);},send(method,params={}){
    return new Promise((resolve,reject)=>{const id=++sequence;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout '+method));},15000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});
  }};
}
async function launch(){
  profile=fs.mkdtempSync(path.join(os.tmpdir(),'raschet-build-chrome-'));
  chrome=spawn(options.chrome,['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe']});
  return await new Promise((resolve,reject)=>{
    let text='';
    const timer=setTimeout(()=>reject(new Error('Chrome startup timeout')),20000);
    chrome.stderr.on('data',data=>{text+=data;const match=text.match(/DevTools listening on (ws:\/\/\S+)/);if(match){clearTimeout(timer);resolve(match[1]);}});
    chrome.once('error',error=>{clearTimeout(timer);reject(error);});
    chrome.once('exit',code=>{clearTimeout(timer);reject(new Error('Chrome early exit '+code+' '+text.slice(-400)));});
  });
}
async function check(browser,endpoint,page){
  const created=await browser.send('Target.createTarget',{url:'about:blank'});
  const targets=await (await fetch(endpoint+'/json/list')).json();
  const target=targets.find(item=>item.id===created.targetId);
  const cdp=await connect(target.webSocketDebuggerUrl);
  const errors=[];
  const origin=new URL(options.url).origin;
  try{
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Network.enable');
    await cdp.send('Network.setBypassServiceWorker',{bypass:true});
    await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
    cdp.on('Runtime.exceptionThrown',p=>errors.push(p.exceptionDetails.exception?.description||p.exceptionDetails.text));
    cdp.on('Runtime.consoleAPICalled',p=>{if(p.type==='error')errors.push(p.args.map(a=>a.value||a.description).join(' '));});
    await cdp.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
    cdp.on('Fetch.requestPaused',p=>{
      const url=new URL(p.request.url);
      const local=url.origin===origin&&['GET','HEAD'].includes(p.request.method)&&!/(?:^|\/)api(?:\/|$)/i.test(url.pathname);
      cdp.send(local?'Fetch.continueRequest':'Fetch.failRequest',local?{requestId:p.requestId}:{requestId:p.requestId,errorReason:'BlockedByClient'}).catch(e=>errors.push('Fetch handler '+e.message));
    });
    await cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:
      'window.__pageErrors=[];addEventListener("unhandledrejection",e=>window.__pageErrors.push(String(e.reason)));Object.defineProperty(navigator,"serviceWorker",{value:{register:()=>Promise.resolve({})},configurable:true});'});
    const loaded=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(new Error('Page load timeout: '+page)),15000);
      cdp.on('Page.loadEventFired',()=>{clearTimeout(timer);resolve();});
    });
    await cdp.send('Page.navigate',{url:new URL(page,options.url).href});
    await loaded;
    const response=await cdp.send('Runtime.evaluate',{awaitPromise:true,returnByValue:true,expression:
      '(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));'+
      'const main=document.getElementById("main-content");const h1=document.querySelector("h1");'+
      'const theme=document.getElementById("theme-toggle");const before=document.documentElement.getAttribute("data-theme");theme?.click();'+
      'const interactive=!!theme&&before!==document.documentElement.getAttribute("data-theme");'+
      'for(const form of document.querySelectorAll("main form"))form.dispatchEvent(new Event("submit",{bubbles:true,cancelable:true}));'+
      'await new Promise(r=>requestAnimationFrame(r));'+
      'return {rendered:!!main&&main.getBoundingClientRect().width>0&&!!h1&&h1.textContent.trim().length>0,interactive,result_found:!!document.querySelector(".result-panel,.compare-output,.groups-output,.password-output,.output"),title:document.title,errors:window.__pageErrors,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth};})()'});
    if(response.exceptionDetails) errors.push(response.exceptionDetails.exception?.description||response.exceptionDetails.text);
    const record=response.result?.value||{};
    return {page,...record,errors:[...errors,...(record.errors||[])]};
  }catch(error){return {page,rendered:false,interactive:false,errors:[...errors,String(error)]};}
  finally{cdp.close();await browser.send('Target.closeTarget',{targetId:created.targetId});}
}
async function main(){
  if(!options.url||!options.pages||!options.result||!options.chrome)throw new Error('Required --url --pages --result --chrome');
  const wsUrl=await launch();
  const endpoint='http://127.0.0.1:'+new URL(wsUrl).port;
  const browser=await connect(wsUrl);
  const pages=JSON.parse(fs.readFileSync(options.pages,'utf8'));
  // Bounded independent tabs, not polling loops; each page awaits load + fonts.
  for(let offset=0;offset<pages.length;offset+=4){
    results.pages.push(...await Promise.all(pages.slice(offset,offset+4).map(page=>check(browser,endpoint,page))));
  }
  results.complete=true;
  browser.close();
}
(async()=>{
  try{await main();}catch(error){results.errors.push(String(error));}
  finally{
    for(const socket of sockets)socket.close();
    if(chrome&&!chrome.killed){const exited=new Promise(r=>chrome.once('exit',r));chrome.kill();await exited;}
    // Profile is an owned mkdtemp path. No unrelated directory is ever removed.
    if(profile)try{fs.rmSync(profile,{recursive:true,force:true});}catch{}
    if(options.result)fs.writeFileSync(options.result,JSON.stringify(results,null,2));
    console.log('Chrome records:',results.pages.length,'errors:',results.errors.length+results.pages.filter(p=>p.errors?.length).length);
    process.exitCode=results.complete&&!results.errors.length&&results.pages.every(p=>p.rendered&&p.interactive&&!p.errors.length)?0:1;
  }
})();
