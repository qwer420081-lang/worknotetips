"""Render reviewed GPT Chat beginner articles without changing existing articles."""
import copy
import json
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('en', 'ko', 'ja', 'es', 'pt-BR')
LABELS = {
 'en': ('Copyable prompts', 'Prompt', 'Check the facts and constraints before using an AI answer.'),
 'ko': ('복사해서 쓰는 요청문', '요청문', 'AI 답변을 사용하기 전에 사실과 조건을 확인하세요.'),
 'ja': ('コピーして使えるプロンプト', 'プロンプト', 'AIの回答を使う前に、事実と条件を確認してください。'),
 'es': ('Instrucciones para copiar', 'Instrucción', 'Comprueba los hechos y las condiciones antes de usar una respuesta de IA.'),
 'pt-BR': ('Prompts para copiar', 'Prompt', 'Confira os fatos e as condições antes de usar uma resposta de IA.'),
}

ROLE_LABELS = {
 'input': {'en':'Sample input','ko':'입력 자료','ja':'入力資料','es':'Datos de entrada','pt-BR':'Dados de entrada'},
 'prompt': {'en':'Prompt','ko':'요청문','ja':'プロンプト','es':'Instrucción','pt-BR':'Prompt'},
 'output': {'en':'Example result','ko':'예시 결과','ja':'結果例','es':'Resultado de ejemplo','pt-BR':'Resultado de exemplo'},
 'bad_output': {'en':'Flawed result','ko':'잘못된 결과','ja':'誤った結果例','es':'Resultado erróneo','pt-BR':'Resultado incorreto'},
 'checklist': {'en':'Checklist','ko':'확인 목록','ja':'確認リスト','es':'Lista de control','pt-BR':'Lista de verificação'},
}

def route(lang, slug):
 return ('/' if lang == 'en' else '/' + lang + '/') + 'articles/' + slug + '/'

def main(batch='beginner-batch', modified='2026-09-21'):
 index=ROOT/'_src/_index.json'; slugs=json.loads(index.read_text(encoding='utf-8'))
 incoming=json.loads((ROOT/'_src'/batch/'en.json').read_text(encoding='utf-8'))['articles']
 for article in incoming:
  if article['slug'] not in slugs: slugs.append(article['slug'])
 total=len(slugs)
 for lang in LANGS:
  data = json.loads((ROOT / '_src' / batch / (lang + '.json')).read_text(encoding='utf-8'))
  assert data['lang'] == lang and data['articles']
  base = ROOT / ('' if lang == 'en' else lang)
  template = (base / 'articles/ai-email-draft-check/index.html').read_text(encoding='utf-8')
  cards = []
  home = BeautifulSoup((base/'index.html').read_text(encoding='utf-8'), 'html.parser')
  for article in data['articles']:
   number=slugs.index(article['slug'])+1
   slug = article['slug']; url = 'https://worknotetips.com' + route(lang, slug)
   doc = BeautifulSoup(template, 'html.parser')
   doc.body['class'] = [*doc.body.get('class',[]),'beginner-article']
   doc.select_one('link[rel="stylesheet"]')['href']='/assets/styles.css?v=20260922-team'
   def tag(name, text=None, **attrs):
    x = doc.new_tag(name, attrs=attrs)
    if text is not None: x.string = str(text)
    return x
   doc.title.string = article['title'] + ' | Worknote'
   for selector, value in [('meta[name="description"]',article['summary']),('meta[property="og:title"]',article['title']),('meta[property="og:description"]',article['summary']),('meta[property="og:url"]',url)]:
    doc.select_one(selector)['content'] = value
   doc.select_one('link[rel="canonical"]')['href'] = url
   for link in doc.select('link[hreflang]'):
    link['href'] = 'https://worknotetips.com' + route('en' if link['hreflang']=='x-default' else link['hreflang'],slug)
   for link in doc.select('a[href]'):
    if '/articles/ai-email-draft-check/' in link['href']:
     link['href'] = link['href'].replace('ai-email-draft-check',slug)
   for script in doc.select('script[type="application/ld+json"]'):
    payload = json.loads(script.string)
    if payload.get('@type') == 'TechArticle':
     payload.update(headline=article['title'],description=article['summary'],url=url,dateModified=modified)
    else:
     for item in payload.get('itemListElement',[]):
      if isinstance(item.get('item'),str) and 'ai-email-draft-check' in item['item']:
       item.update(name=article['title'],item=url)
    script.string = json.dumps(payload, ensure_ascii=False)
   doc.h1.string = article['title']
   doc.select_one('.article-summary').string = article['summary']
   doc.select_one('.article-meta').find_all('span')[-1].string = LABELS[lang][0]
   meta_date=doc.select_one('.article-meta').find('span')
   meta_date.string=re.sub(r'\d{4}\.\d{2}\.\d{2}',modified.replace('-','.'),meta_date.text)
   doc.select_one('.aside-note').string = LABELS[lang][2]
   messages=doc.select_one('#ui-messages'); ui=json.loads(messages.string)
   ui['copySuccess']={'en':'Example text copied.','ko':'예시 텍스트를 복사했습니다.','ja':'例文をコピーしました。','es':'Texto de ejemplo copiado.','pt-BR':'Texto de exemplo copiado.'}[lang]
   messages.string=json.dumps(ui,ensure_ascii=False)
   footer_ps = doc.select('footer p')
   if footer_ps: footer_ps[-1].string = LABELS[lang][2]
   reading = doc.select_one('.reading-content')
   setup = copy.deepcopy(reading.select_one('.reader-setup'))
   p = setup.find('p'); strong = copy.deepcopy(p.strong); p.clear(); p.append(strong); p.append(article['audience'])
   ul = setup.find('ul'); ul.clear()
   for value in article['prerequisites']: ul.append(tag('li',value))
   ver = copy.deepcopy(reading.select_one('#verification'))
   verification_heading = {'en':'What to check yourself','ko':'직접 확인할 항목','ja':'自分で確認する項目','es':'Qué comprobar por tu cuenta','pt-BR':'O que conferir por conta própria'}[lang]
   limit_label = ver.select_one('.verification-limits strong').get_text()
   reading.clear(); reading.append(setup)
   toc = []
   for i, section in enumerate(article['sections'],1):
    heading = re.sub(r'^\d+[.、．]\s*','',section['heading'])
    el = tag('section',id=section['id']); h = tag('h2'); h.append(tag('span',f'{i:02}',**{'class':'section-number'})); h.append(heading); el.append(h); toc.append((section['id'],heading))
    for j, block in enumerate(section['blocks'],1):
     kind = block['type']
     if kind == 'p': el.append(tag('p',block['text']))
     elif kind == 'ul':
      ul=tag('ul')
      for value in block['items']: ul.append(tag('li',value))
      el.append(ul)
     elif kind == 'code':
      ident=f'prompt-{i}-{j}'; wrapper=tag('div',**{'class':'code-block'}); bar=tag('div',**{'class':'code-toolbar'})
      label = {'en':'Editorial example','ko':'편집 예시','ja':'編集例','es':'Ejemplo editorial','pt-BR':'Exemplo editorial'}[lang] if block['text'].startswith('[') else LABELS[lang][1]
      if block.get('role') in ROLE_LABELS: label = ROLE_LABELS[block['role']][lang]
      bar.append(tag('span',label)); button=tag('button',ui['copy'],type='button',**{'data-copy':ident,'aria-label':ui['copy']+' '+label}); bar.append(button)
      pre=tag('pre',tabindex='0',dir='auto'); pre.append(tag('code',block['text'],id=ident)); wrapper.extend([bar,pre]); el.append(wrapper)
     elif kind == 'table':
      wrapper=tag('div',**{'class':'table-wrap wide' if len(block['headers'])>=5 else 'table-wrap'}); table=tag('table'); head=tag('thead'); tr=tag('tr')
      for value in block['headers']: tr.append(tag('th',value,scope='col'))
      head.append(tr); table.append(head); body=tag('tbody')
      for row in block['rows']:
       assert len(row)==len(block['headers'])
       tr=tag('tr')
       for value in row: tr.append(tag('td',value))
       body.append(tr)
      table.append(body); wrapper.append(table); el.append(wrapper)
     else: raise ValueError(kind)
    reading.append(el)
   v=article['verification']; ver.clear(); ver.append(tag('h2',verification_heading)); ver.append(tag('p',v['env'])); ul=tag('ul')
   for value in v['items']: ul.append(tag('li',value))
   ver.append(ul); limits=tag('div',**{'class':'verification-limits'}); limits.append(tag('strong',limit_label))
   limits.append(tag('p',v['limits'] if isinstance(v['limits'],str) else ' '.join(v['limits']))); ver.append(limits); reading.append(ver); toc.append(('verification',verification_heading))
   for ol in doc.select('.toc ol'):
    ol.clear()
    for i,(ident,heading) in enumerate(toc,1):
     li=tag('li'); a=tag('a',href='#'+ident); a.append(tag('span',f'{i:02}')); a.append(heading); li.append(a); ol.append(li)
   related=doc.select_one('.related .article-grid'); related.clear()
   for other in data['articles']:
    if other['slug'] != slug:
     item=tag('article',**{'class':'article-card'}); h=tag('h3'); h.append(tag('a',other['title'],href=route(lang,other['slug']))); item.append(h); item.append(tag('p',other['summary'])); related.append(item)
   dest=base/'articles'/slug/'index.html'; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(str(doc),encoding='utf-8')
   card=copy.deepcopy(home.select_one('.article-card[data-category="ai"]'))
   card['data-search']=unicodedata.normalize('NFKC',' '.join([article['title'],article['summary'],*article['tags']])).lower()
   card.select_one('.article-number').string=str(number); card.h3.a.string=article['title']; card.h3.a['href']=route(lang,slug); card.find('p').string=article['summary']; tags=card.select_one('.tags'); tags.clear()
   for value in article['tags']: tags.append(tag('span',value))
   cards.append(card)
   if lang=='en': (ROOT/'_src'/f'{slug}.json').write_text(json.dumps(article,ensure_ascii=False,indent=2),encoding='utf-8')
  for target in (base/'index.html',base/'category/ai/index.html'):
   page=BeautifulSoup(target.read_text(encoding='utf-8'),'html.parser'); grid=page.select_one('main .article-grid')
   for card in list(grid.select('.article-card')):
    if any(card.select_one('h3 a')['href']==route(lang,a['slug']) for a in data['articles']): card.decompose()
   for card in reversed(cards): grid.insert(0,copy.deepcopy(card))
   count=len(grid.select('.article-card')); page.select_one('#result-count').string=str(count)
   note=page.select_one('.list-heading p')
   if note:
    note.string=re.sub(r'\d+(?!.*\d)',str(count),note.get_text())
   target.write_text(str(page),encoding='utf-8')
  for target in [base/'index.html',*base.glob('category/*/index.html')]:
   page=BeautifulSoup(target.read_text(encoding='utf-8'),'html.parser')
   for link in page.select('.category-rail a[href]'):
    count=link.select_one('.count')
    if count and link['href']==('/' if lang=='en' else '/'+lang+'/'): count.string=str(total)
    if count and link['href'].endswith('/category/ai/'):
     ai_page=BeautifulSoup((base/'category/ai/index.html').read_text(encoding='utf-8'),'html.parser')
     count.string=ai_page.select_one('#result-count').text
   target.write_text(str(page),encoding='utf-8')
 index.write_text(json.dumps(sorted(slugs),ensure_ascii=False),encoding='utf-8')
 ns='http://www.sitemaps.org/schemas/sitemap/0.9'; ET.register_namespace('',ns); path=ROOT/'sitemap.xml'; tree=ET.parse(path); root=tree.getroot(); existing={e.text for e in root.findall('{'+ns+'}url/{'+ns+'}loc')}
 for lang in LANGS:
  for a in data['articles']:
   url='https://worknotetips.com'+route(lang,a['slug'])
   if url not in existing:
    e=ET.SubElement(root,'{'+ns+'}url'); ET.SubElement(e,'{'+ns+'}loc').text=url; ET.SubElement(e,'{'+ns+'}lastmod').text=modified
 tree.write(path,encoding='utf-8',xml_declaration=True)
 print(f'Built {len(incoming)*len(LANGS)} articles; updated {2*len(LANGS)} indexes and sitemap.')

if __name__ == '__main__': main()
