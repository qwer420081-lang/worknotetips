const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../assets/app.js'),'utf8');
const analytics=source.split('const input=document.querySelector')[0];
function run({url='https://worknotetips.com/ko/?q=private-text',stored=null,blocked=false}={}){
 const scripts=[],events={},docEvents={};let value=stored,replacement;
 const location=new URL(url);location.replace=next=>{replacement=next;};
 const status={dataset:{off:'OFF',on:'ON'},textContent:''};
 const buttons=['off','on'].map(value=>({dataset:{analyticsChoice:value},setAttribute(){},addEventListener(name,fn){this[name]=fn;}}));
 const document={documentElement:{lang:'ko'},referrer:'https://example.com/path/?secret=123',
  head:{appendChild:s=>scripts.push(s)},createElement:()=>({}),
  querySelectorAll:selector=>selector==='[data-analytics-status]'?[status]:selector==='[data-analytics-choice]'?buttons:[],
  addEventListener:(name,fn)=>docEvents[name]=fn};
 const context={location,document,URL,URLSearchParams,Date,localStorage:{getItem(){if(blocked)throw Error();return value;},setItem(k,v){if(blocked)throw Error();value=v;}},
  history:{replaceState(a,b,path){const next=new URL(path,location);location.href=next.href;}},addEventListener:(name,fn)=>events[name]=fn};
 context.window=context;vm.runInNewContext(analytics,context);
 return {context,scripts,events,docEvents,status,buttons,get value(){return value;},get replacement(){return replacement;}};
}
let r=run();assert.equal(r.scripts.length,1);
let config=r.context.dataLayer[1][2];assert.equal(config.page_location,'https://worknotetips.com/ko/');assert.equal(config.page_referrer,'https://example.com/path/');
r.context.worknoteTrack('example_copy',{article_id:'ai-clear-request'});assert.equal(r.context.dataLayer[2][1],'example_copy');
assert.equal(r.context.dataLayer[2][2].content_language,'ko');assert.ok(!JSON.stringify(r.context.dataLayer).includes('private-text'));
r.docEvents.click({target:{closest:()=>({href:'https://worknotetips.com/ko/articles/ai-clear-request/?ignored=secret',hasAttribute:()=>true})}});
assert.equal(r.context.dataLayer[3][1],'starter_select');assert.equal(r.context.dataLayer[3][2].article_id,'ai-clear-request');
r.docEvents.click({target:{closest:()=>({href:'https://external.example/articles/ai-clear-request/',hasAttribute:()=>true})}});assert.equal(r.context.dataLayer.length,4);
r.buttons[0].click();assert.equal(r.value,'1');assert.equal(r.context['ga-disable-G-NZFH8DJJJ5'],true);assert.match(r.replacement,/internal=1/);
r.context.worknoteTrack('example_copy',{});assert.equal(r.context.dataLayer.length,4);
for(const options of [{stored:'1'},{url:'https://worknotetips.com/?internal=1&q=secret'},{url:'https://worknotetips.com/?internal=1',blocked:true},{url:'http://localhost:8765/ko/'}]){
 r=run(options);assert.equal(r.scripts.length,0);r.context.worknoteTrack('example_copy',{});assert.equal(r.context.dataLayer,undefined);
}
r=run({stored:'1',url:'https://worknotetips.com/ko/?internal=0#section'});assert.equal(r.scripts.length,1);assert.equal(r.value,'0');assert.equal(r.context.location.hash,'#section');assert.equal(r.context.location.search,'');
console.log('PASS: exclusion before GA load, persistence, storage denial, resume, query sanitization, local preview, safe click/copy events. No network requests made.');
