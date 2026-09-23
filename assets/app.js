if(location.protocol==='http:'&&location.hostname==='worknotetips.com'){location.replace('https://'+location.host+location.pathname+location.search+location.hash);}
(function(){
 const id='G-NZFH8DJJJ5', key='worknote.analytics.disabled';
 const params=new URLSearchParams(location.search);
 let disabled=false;
 try{disabled=localStorage.getItem(key)==='1';}catch{}
 // Editors can exclude this browser before the first analytics request.
 if(params.get('internal')==='1'||params.get('internal')==='0'){
  disabled=params.get('internal')==='1';
  try{localStorage.setItem(key,disabled?'1':'0');}catch{}
  params.delete('internal');
  history.replaceState(null,'',location.pathname+(params.size?'?'+params:'')+location.hash);
 }
 window['ga-disable-'+id]=disabled;
 function status(){
  document.querySelectorAll('[data-analytics-status]').forEach(el=>el.textContent=disabled?el.dataset.off:el.dataset.on);
  document.querySelectorAll('[data-analytics-choice]').forEach(el=>el.setAttribute('aria-pressed',String((el.dataset.analyticsChoice==='off')===disabled)));
 }
 status();
 document.querySelectorAll('[data-analytics-choice]').forEach(button=>button.addEventListener('click',()=>{
  disabled=button.dataset.analyticsChoice==='off';window['ga-disable-'+id]=disabled;
  try{localStorage.setItem(key,disabled?'1':'0');}catch{}
  status();
  // The URL also carries the choice when browser storage is unavailable.
  const next=new URL(location.href);next.searchParams.set('internal',disabled?'1':'0');location.replace(next.href);
 }));
 window.addEventListener('storage',event=>{if(event.key===key||event.key===null){try{disabled=localStorage.getItem(key)==='1';}catch{return;}window['ga-disable-'+id]=disabled;status();}});
 window.worknoteTrack=function(name,fields){
  if(disabled||location.hostname!=='worknotetips.com'||!window.gtag)return;
  window.gtag('event',name,{content_language:document.documentElement.lang,...fields});
 };
 if(location.hostname!=='worknotetips.com'||disabled)return;
 const script=document.createElement('script');script.async=true;script.src='https://www.googletagmanager.com/gtag/js?id='+id;
 window.dataLayer=window.dataLayer||[];window.gtag=function(){window.dataLayer.push(arguments);};
 window.gtag('js',new Date());
 // Search terms and inspection parameters do not belong in page URLs sent to GA.
 let referrer='';try{const ref=new URL(document.referrer);referrer=ref.origin+ref.pathname;}catch{}
 window.gtag('config',id,{anonymize_ip:true,page_location:location.origin+location.pathname,page_referrer:referrer});
 document.head.appendChild(script);
})();

document.addEventListener('click',event=>{
 const link=event.target.closest?.('a[href]');if(!link)return;
 const url=new URL(link.href,location.href);
 const match=url.pathname.match(/^\/(?:ko\/|ja\/|es\/|pt-BR\/)?articles\/([a-z0-9-]+)\/$/);
 if(url.origin===location.origin&&match)window.worknoteTrack(link.hasAttribute('data-starter')?'starter_select':'tutorial_open',{article_id:match[1]});
});

const input=document.querySelector('#search-input');
const form=document.querySelector('#search');
const cards=[...document.querySelectorAll('.article-card[data-search]')];
const messages=JSON.parse(document.querySelector('#ui-messages').textContent);
let announcementTimer;
function normalize(value){return value.normalize('NFKC').toLocaleLowerCase(document.documentElement.lang).trim();}
function filterSearch({update=true}={}){
 if(!input)return;
 const words=normalize(input.value).split(/\s+/).filter(Boolean);
 let count=0;
 for(const card of cards){const matched=words.every(word=>card.dataset.search.includes(word));card.hidden=!matched;if(matched)count++;}
 document.querySelector('#result-count').textContent=count;
 document.querySelector('#empty-state').hidden=count!==0;
 document.querySelector('#search-reset').hidden=!input.value;
 clearTimeout(announcementTimer);
 announcementTimer=setTimeout(()=>{document.querySelector('#search-status').textContent=messages.searchCount.replace('{count}',count);},200);
 if(update){const query=new URLSearchParams(location.search);query.delete('q');history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+(input.value?'#q='+encodeURIComponent(input.value):''));}
}
function restoreSearch(){if(!input)return;const hash=location.hash.slice(1);input.value=(hash.startsWith('q=')?new URLSearchParams(hash).get('q'):new URLSearchParams(location.search).get('q'))||'';filterSearch({update:false});}
input?.addEventListener('input',()=>filterSearch());
form?.addEventListener('submit',event=>{event.preventDefault();filterSearch();});
form?.addEventListener('reset',event=>{event.preventDefault();input.value='';filterSearch();input.focus();});
document.querySelector('#empty-reset')?.addEventListener('click',()=>form.reset());
window.addEventListener('hashchange',restoreSearch);
window.addEventListener('pageshow',restoreSearch);
restoreSearch();
document.addEventListener('keydown',event=>{if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)){if(input){event.preventDefault();input.focus();}}});
let toastTimer;
function toast(message){const el=document.querySelector('#toast');el.textContent=message;el.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.hidden=true,3500);}
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
 const text=document.getElementById(button.dataset.copy).textContent;
 try {
  if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);
  else {const area=document.createElement('textarea');area.value=text;area.setAttribute('readonly','');area.style.position='fixed';area.style.top='-10000px';document.body.append(area);area.select();const success=document.execCommand('copy');area.remove();button.focus();if(!success)throw new Error('Copy denied');}
  const article=location.pathname.match(/\/articles\/([a-z0-9-]+)\/$/);if(article)window.worknoteTrack('example_copy',{article_id:article[1]});
  button.textContent=messages.copied;toast(messages.copySuccess);setTimeout(()=>button.textContent=messages.copy,2500);
 }catch{button.textContent=messages.copyRetry;toast(messages.copyFailure);}
}));
if('IntersectionObserver' in window){const links=[...document.querySelectorAll('.article-aside .toc a[href^="#"]')];const observer=new IntersectionObserver(entries=>{const visible=entries.filter(entry=>entry.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];if(visible)for(const link of links){if(link.hash==='#'+visible.target.id)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');}},{rootMargin:'-15% 0px -60% 0px',threshold:0});document.querySelectorAll('.reading-content section[id]').forEach(section=>observer.observe(section));}
