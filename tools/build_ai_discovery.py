"""Publish AI foundations and question-led routes into practical tutorials."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from build_beginner_articles import main as build, LANGS, route
ROOT=Path(__file__).resolve().parents[1]
THEORY='generative-ai-basics'
SOURCES=[('NIST AI 600-1: Generative Artificial Intelligence Profile','https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf'),('Google Research: Transformer — A Novel Neural Network Architecture for Language Understanding','https://research.google/blog/transformer-a-novel-neural-network-architecture-for-language-understanding/')]
def main():
 build('theory-batch','2026-09-22')
 changed=set()
 for lang in LANGS:
  data=json.loads((ROOT/'_src/theory-batch'/f'{lang}.json').read_text(encoding='utf-8'))
  article=data['articles'][0]; discovery=data['discovery']; base=ROOT/('' if lang=='en' else lang)
  targets=[base/'category/ai/index.html',base/'articles'/THEORY/'index.html',*[base/'articles'/x['slug']/'index.html' for x in discovery['links']]]
  for p in targets:
   doc=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
   doc.select_one('link[rel="stylesheet"]')['href']='/assets/styles.css?v=20260922-team'
   def tag(name,text=None,**attrs):
    el=doc.new_tag(name,attrs=attrs)
    if text is not None: el.string=text
    return el
   previous=doc.find(id='explore-ai')
   if previous: previous.decompose()
   box=tag('section',id='explore-ai',**{'class':'ai-discovery','aria-labelledby':'explore-ai-title'})
   box.append(tag('h2',discovery['heading'],id='explore-ai-title')); box.append(tag('p',discovery['intro']))
   if p.parent.name!=THEORY:
    intro=tag('p'); intro.append(discovery['theoryLabel']+': '); intro.append(tag('a',article['title'],href=route(lang,THEORY))); box.append(intro)
   ul=tag('ul')
   for link in discovery['links']:
    if p.parent.name==link['slug']: continue
    li=tag('li'); li.append(tag('a',link['question'],href=route(lang,link['slug']))); li.append(tag('p',link['benefit'])); ul.append(li)
   box.append(ul)
   if '/category/' in p.as_posix(): doc.select_one('.page-intro').insert_after(box)
   else:
    doc.select_one('.related').insert_before(box)
    if p.parent.name==THEORY:
     doc.select_one('.article-header .category-badge').string={'en':'AI foundations','ko':'AI 기초 이론','ja':'AIの基礎','es':'Fundamentos de IA','pt-BR':'Fundamentos de IA'}[lang]
     doc.select_one('.related').decompose()
     references=tag('section',id='references',**{'class':'references'})
     references.append(tag('h2',{'en':'Sources and further reading','ko':'근거 자료와 더 읽을거리','ja':'参考資料と関連資料','es':'Fuentes y lecturas adicionales','pt-BR':'Fontes e leituras adicionais'}[lang]))
     ul=tag('ul')
     for title,url in SOURCES:
      li=tag('li'); li.append(tag('a',title,href=url)); ul.append(li)
     references.append(ul); doc.select_one('.reading-content').append(references)
     for ol in doc.select('.toc ol'):
      li=tag('li'); li.append(tag('a',references.h2.text,href='#references')); ol.append(li)
   p.write_text(str(doc),encoding='utf-8',newline=''); changed.add('https://worknotetips.com/'+p.parent.relative_to(ROOT).as_posix()+'/')
  for p in [base/'index.html',*base.glob('category/*/index.html')]:
   relative=p.parent.relative_to(ROOT).as_posix(); changed.add('https://worknotetips.com/'+('' if relative=='.' else relative+'/'))
 ns='http://www.sitemaps.org/schemas/sitemap/0.9'; ET.register_namespace('',ns); p=ROOT/'sitemap.xml'; tree=ET.parse(p)
 for el in tree.getroot():
  if el.find('{'+ns+'}loc').text in changed: el.find('{'+ns+'}lastmod').text='2026-09-22'
 tree.write(p,encoding='utf-8',xml_declaration=True)
 print('Published theory in 5 languages and 30 question-led discovery sections.')
if __name__=='__main__': main()
