// Offline worker unit checks: aliases, no query/API/private/runtime caching.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const site=process.argv[2];
if(!site)throw new Error('Usage: node tests/build_sw.js OUT');
let assertions=0;
const handlers={};
const matches=[];
let writes=0;
const scope='https://unit.invalid/sub/';
const context=vm.createContext({URL,Headers,Request,Set,Promise,console,
  self:{registration:{scope},location:{origin:'https://unit.invalid'},clients:{claim:async()=>{}},skipWaiting:async()=>{},addEventListener:(name,handler)=>handlers[name]=handler},
  caches:{open:async()=>({match:async key=>{matches.push(key);return {cached:key};},put:async()=>writes++}),keys:async()=>[],delete:async()=>true},
  fetch:async()=>{throw new Error('offline');}
});
vm.runInContext(fs.readFileSync(path.join(site,'sw.js'),'utf8'),context);
async function request(url,extra={}){
  let response;
  handlers.fetch({request:{url:new URL(url,scope).href,method:'GET',mode:'navigate',headers:new Headers(),cache:'default',...extra},respondWith:value=>response=value});
  return response===undefined?undefined:await response;
}
function equal(actual,expected){assert.equal(actual,expected);assertions++;}
(async()=>{
  for(const [url,key] of [['./',scope],['index.html',scope],['procenty/',scope+'procenty/'],['procenty/index.html',scope+'procenty/'],['assets/icon-192.png',scope+'assets/icon-192.png']]){
    equal((await request(url,{mode:url.includes('assets/')?'cors':'navigate'})).cached,key);
  }
  for(const url of ['?share=fake','index.html?share=fake','procenty/index.html?secret=fake','api/feedback','api/rates','unknown/','https://external.invalid/']){
    const before=matches.length;equal(await request(url),undefined);equal(matches.length,before);
  }
  for(const extra of [{method:'POST'},{method:'HEAD'},{headers:new Headers({authorization:'Bearer fake'})},{cache:'no-store'}])equal(await request('./',extra),undefined);
  equal(writes,0);
  for(const headers of [{'cache-control':'private'},{'cache-control':'no-store'},{'cache-control':'no-cache'},{vary:'*'},{'set-cookie':'fake=1'}]){
    context.response={ok:true,redirected:false,type:'basic',headers:new Headers(headers)};
    equal(vm.runInContext('publicResponse(response)',context),false);
  }
  context.response={ok:true,redirected:false,type:'basic',headers:new Headers()};equal(vm.runInContext('publicResponse(response)',context),true);
  context.response.redirected=true;equal(vm.runInContext('publicResponse(response)',context),false);
  console.log('PASS worker safety:',assertions,'assertions');
})().catch(error=>{console.error(error);process.exitCode=1;});
