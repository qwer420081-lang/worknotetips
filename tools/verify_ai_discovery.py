"""Check theory translations, copied prompts, and exploration navigation."""
import json
from pathlib import Path
from bs4 import BeautifulSoup
from build_ai_discovery import THEORY, LANGS, route
ROOT=Path(__file__).resolve().parents[1]
def main():
 baseline=None; sections=0
 for lang in LANGS:
  data=json.loads((ROOT/'_src/theory-batch'/f'{lang}.json').read_text(encoding='utf-8'))
  a=data['articles'][0]; assert a['slug']==THEORY
  structure=[(s['id'],[b['type'] for b in s['blocks']]) for s in a['sections']]
  if baseline is None: baseline=structure
  assert structure==baseline,(lang,'translation structure')
  p=ROOT/route(lang,THEORY).strip('/')/'index.html'; doc=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
  assert doc.h1.text==a['title'] and doc.html['lang']==lang
  expected=[b['text'] for s in a['sections'] for b in s['blocks'] if b['type']=='code']
  assert len(expected)>=1 and [x.text for x in doc.select('pre code')]==expected
  assert len(doc.select('#references a'))==2 and len(doc.select('link[hreflang]'))==6
  base=ROOT/('' if lang=='en' else lang)
  paths=[base/'category/ai/index.html',p,*[base/'articles'/x['slug']/'index.html' for x in data['discovery']['links']]]
  for page in paths:
   doc=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser'); boxes=doc.select('#explore-ai'); assert len(boxes)==1
   for link in boxes[0].select('a'):
    target=ROOT/link['href'].strip('/')/'index.html'
    assert target.exists() and target!=page
   sections+=1
  for page,count in [(base/'index.html','57'),(base/'category/ai/index.html','26')]:
   doc=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser'); assert doc.select_one('#result-count').text==count
 print(json.dumps({'theory_pages':5,'discovery_sections':sections,'translations_structure':'PASS','prompt_rendering':'PASS','related_routes_and_counts':'PASS'},indent=2))
if __name__=='__main__': main()
