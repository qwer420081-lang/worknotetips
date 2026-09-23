"""Publish reviewed Chat drafts and append localized report prompts."""
import json
import re
import unicodedata
from pathlib import Path
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from build_beginner_articles import main as build, LANGS, route, ROLE_LABELS

ROOT=Path(__file__).resolve().parents[1]
DATE='2026-09-23'
NEW='ai-presentation-outline'

def main():
    build('keyword-batch',DATE)
    for lang in LANGS:
        data=json.loads((ROOT/'_src/keyword-batch'/f'{lang}.json').read_text(encoding='utf-8'))
        base=ROOT/('' if lang=='en' else lang)
        for patch in data['patches']:
            path=base/'articles'/patch['slug']/'index.html'
            doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            doc.title.string=patch['title']+' | Worknote'
            doc.h1.string=patch['title']
            doc.select_one('.article-summary').string=patch['summary']
            for selector,key in [('meta[name="description"]','summary'),('meta[property="og:title"]','title'),('meta[property="og:description"]','summary')]:
                doc.select_one(selector)['content']=patch[key]
            for script in doc.select('script[type="application/ld+json"]'):
                obj=json.loads(script.string)
                if obj.get('@type')=='TechArticle': obj.update(headline=patch['title'],description=patch['summary'],dateModified=DATE)
                else:
                    for item in obj.get('itemListElement',[]):
                        if isinstance(item.get('item'),str) and route(lang,patch['slug']) in item['item']: item['name']=patch['title']
                script.string=json.dumps(obj,ensure_ascii=False)
            meta=doc.select_one('.article-meta').find('span')
            meta.string=re.sub(r'\d{4}\.\d{2}\.\d{2}',DATE.replace('-','.'),meta.text)
            old=doc.find(id='report-prompt')
            if old: old.decompose()
            def tag(name,text=None,**attrs):
                el=doc.new_tag(name,attrs=attrs)
                if text is not None: el.string=text
                return el
            section=tag('section',id='report-prompt')
            section.append(tag('h2',patch['heading']))
            section.append(tag('p',patch['paragraph']))
            wrapper=tag('div',**{'class':'code-block'})
            bar=tag('div',**{'class':'code-toolbar'})
            bar.append(tag('span',ROLE_LABELS['prompt'][lang]))
            ui=json.loads(doc.select_one('#ui-messages').string)
            bar.append(tag('button',ui['copy'],type='button',**{'data-copy':'localized-report-prompt'}))
            wrapper.append(bar); pre=tag('pre',tabindex='0',dir='auto',style='white-space:pre-wrap;overflow-wrap:anywhere')
            pre.append(tag('code',patch['prompt'],id='localized-report-prompt'))
            wrapper.append(pre); section.append(wrapper)
            doc.select_one('#verification').insert_before(section)
            for ol in doc.select('.toc ol'):
                if not ol.select_one('a[href="#report-prompt"]'):
                    li=tag('li'); li.append(tag('a',patch['heading'],href='#report-prompt')); ol.append(li)
            path.write_text(str(doc),encoding='utf-8')
        articles=[data['articles'][0],*data['patches']]
        # Update cards and descriptive links wherever the edited titles appear.
        for path in base.rglob('index.html'):
            if lang=='en' and path.relative_to(base).parts[0] in LANGS[1:]: continue
            doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser'); changed=False
            for card in doc.select('.article-card[data-category="ai"]'):
                a=card.select_one('h3 a')
                if a and a.get('href')==route(lang,NEW):
                    card.select_one('.article-number').string='74'; changed=True
            for patch in data['patches']:
                for card in doc.select('.article-card'):
                    a=card.select_one('h3 a')
                    if a and a.get('href')==route(lang,patch['slug']):
                        a.string=patch['title']; card.find('p').string=patch['summary']; changed=True
                        if card.has_attr('data-search'): card['data-search']=unicodedata.normalize('NFKC',patch['title']+' '+patch['summary']+' '+card.get_text(' ',strip=True)).lower()
            if changed: path.write_text(str(doc),encoding='utf-8')
        # Connect presentation writing to the existing reporting workflow in both directions.
        for article in articles:
            path=base/'articles'/article['slug']/'index.html'; doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            if article['slug']==NEW:
                for script in doc.select('script[type="application/ld+json"]'):
                    obj=json.loads(script.string)
                    if obj.get('@type')=='TechArticle':
                        obj['datePublished']=DATE
                        script.string=json.dumps(obj,ensure_ascii=False)
            grid=doc.select_one('.related .article-grid')
            for other in articles:
                if other['slug']==article['slug'] or grid.select_one('a[href="'+route(lang,other['slug'])+'"]'): continue
                card=doc.new_tag('article',attrs={'class':'article-card'}); h=doc.new_tag('h3'); a=doc.new_tag('a',href=route(lang,other['slug'])); a.string=other['title']; h.append(a); card.append(h); p=doc.new_tag('p'); p.string=other['summary']; card.append(p); grid.append(card)
            path.write_text(str(doc),encoding='utf-8')
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'; ET.register_namespace('',ns)
    sitemap=ROOT/'sitemap.xml'; tree=ET.parse(sitemap)
    targets={'https://worknotetips.com'+route(l,s) for l in LANGS for s in [NEW,'ai-report-review','ai-weekly-report-from-log']}
    targets.update('https://worknotetips.com'+('/' if l=='en' else '/'+l+'/')+suffix for l in LANGS for suffix in ['','category/ai/'])
    for el in tree.getroot():
        if el.find('{'+ns+'}loc').text in targets: el.find('{'+ns+'}lastmod').text=DATE
    tree.write(sitemap,encoding='utf-8',xml_declaration=True)
    print('Built 5 presentation articles; updated 10 report articles and related cards.')

if __name__=='__main__': main()
