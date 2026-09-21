"""Check rendered prompt text, translation structure and worked arithmetic."""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from build_beginner_articles import LANGS, route

ROOT=Path(__file__).resolve().parents[1]
def numbers(row):
 text=str(row)
 for pattern in (r'October 12',r'12 de octubre',r'12 de outubro',r'10月\s*12日',r'10월\s*12일'):
  text=re.sub(pattern,'10-12',text,flags=re.I)
 return sorted(re.findall(r'\d+(?:[.,]\d+)?',text.replace('0,25','0.25')))
def main():
 source=ROOT/'_src/beginner-batch'
 original=json.loads((source/'ko.json').read_text(encoding='utf-8'))['articles']
 pages=0; prompts=0
 for lang in LANGS:
  articles=json.loads((source/(lang+'.json')).read_text(encoding='utf-8'))['articles']
  assert [a['slug'] for a in articles]==[a['slug'] for a in original]
  for baseline,a in zip(original,articles):
   assert [s['id'] for s in a['sections']]==[s['id'] for s in baseline['sections']]
   for bs,s in zip(baseline['sections'],a['sections']):
    assert [b['type'] for b in bs['blocks']]==[b['type'] for b in s['blocks']],(lang,a['slug'],s['id'])
    for b,t in zip(bs['blocks'],s['blocks']):
     if b['type']=='table':
      assert len(b['rows'])==len(t['rows'])
      assert [numbers(row) for row in b['rows']]==[numbers(row) for row in t['rows']],(lang,a['slug'],'table numbers')
   path=ROOT/route(lang,a['slug']).strip('/')/'index.html'
   doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
   expected=[b['text'] for s in a['sections'] for b in s['blocks'] if b['type']=='code']
   assert [b.get_text() for b in doc.select('pre code')]==expected
   assert len(doc.select('[data-copy]'))==len(expected)
   for button in doc.select('[data-copy]'): assert doc.find(id=button['data-copy'])
   assert doc.h1.text==a['title'] and doc.html['lang']==lang
   assert doc.select_one('link[rel="canonical"]')['href']=='https://worknotetips.com'+route(lang,a['slug'])
   assert len(doc.select('link[hreflang]'))==6
   for link in doc.select('link[hreflang]'): assert a['slug'] in link['href']
   pages+=1; prompts+=len(expected)
 assert 80*.25==20 and 200*(1-.15)==170 and (50-40)/40*100==25
 capacity=[30,0,45,30,0,60,30]; use=[25,0,45,30,0,55,20]
 assert sum(capacity)==195 and sum(use)==175 and all(a<=b for a,b in zip(use,capacity))
 assert sum(capacity)-sum(use)==20 and 20*2+25*3+30*2==175
 assert sum(capacity)-45==150 and 175-25==150
 print(json.dumps({'new_pages':pages,'copyable_blocks':prompts,'translation_structure_and_table_numbers':'PASS','worked_arithmetic_and_day_limits':'PASS'},indent=2))
if __name__=='__main__': main()
