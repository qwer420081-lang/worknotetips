"""Build eight reviewed everyday-AI tutorials in five languages."""
import json
from pathlib import Path
from bs4 import BeautifulSoup
from build_beginner_articles import main as build,LANGS,route
ROOT=Path(__file__).resolve().parents[1]
DATE='2026-09-23'

def main():
    build('expansion-batch',DATE)
    for lang in LANGS:
        articles=json.loads((ROOT/'_src/expansion-batch'/f'{lang}.json').read_text(encoding='utf-8'))['articles']
        base=ROOT/('' if lang=='en' else lang)
        for article in articles:
            path=ROOT/route(lang,article['slug']).strip('/')/'index.html'
            doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            for script in doc.select('script[type="application/ld+json"]'):
                data=json.loads(script.string)
                if data.get('@type')=='TechArticle':
                    data['datePublished']=DATE
                    script.string=json.dumps(data,ensure_ascii=False)
            path.write_text(str(doc),encoding='utf-8')
        for path in [base/'index.html',base/'category/ai/index.html']:
            doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            for i,article in enumerate(articles,75):
                card=doc.select_one('.article-card:has(a[href="'+route(lang,article['slug'])+'"])')
                card.select_one('.article-number').string=str(i)
            path.write_text(str(doc),encoding='utf-8')
    print('Built 40 pages, 82 topics total.')

if __name__=='__main__': main()
