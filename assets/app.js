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
 if(update)history.replaceState(null,'',location.pathname+location.search+(input.value?'#q='+encodeURIComponent(input.value):''));
}
function restoreSearch(){if(!input)return;const hash=location.hash.slice(1);input.value=hash.startsWith('q=')?new URLSearchParams(hash).get('q')||'':'';filterSearch({update:false});}
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
  button.textContent=messages.copied;toast(messages.copySuccess);setTimeout(()=>button.textContent=messages.copy,2500);
 }catch{button.textContent=messages.copyRetry;toast(messages.copyFailure);}
}));
if('IntersectionObserver' in window){const links=[...document.querySelectorAll('.article-aside .toc a[href^="#"]')];const observer=new IntersectionObserver(entries=>{const visible=entries.filter(entry=>entry.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];if(visible)for(const link of links){if(link.hash==='#'+visible.target.id)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');}},{rootMargin:'-15% 0px -60% 0px',threshold:0});document.querySelectorAll('.reading-content section[id]').forEach(section=>observer.observe(section));}
