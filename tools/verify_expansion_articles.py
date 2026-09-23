"""Validate publication structure and worked examples in the expansion batch."""
import json,re
from pathlib import Path
from fractions import Fraction
from collections import Counter
from bs4 import BeautifulSoup
from build_beginner_articles import LANGS,route
ROOT=Path(__file__).resolve().parents[1]

def shape(a):
    return [(s['id'],[(b['type'],len(b.get('rows',[])),len(b.get('headers',[])),len(b.get('items',[]))) for b in s['blocks']]) for s in a['sections']]

def main():
    baseline=json.loads((ROOT/'_src/expansion-batch/ko.json').read_text(encoding='utf-8'))['articles']
    pages=blocks=0
    for lang in LANGS:
        articles=json.loads((ROOT/'_src/expansion-batch'/f'{lang}.json').read_text(encoding='utf-8'))['articles']
        assert [a['slug'] for a in articles]==[a['slug'] for a in baseline]
        for original,a in zip(baseline,articles):
            assert shape(a)==shape(original),(lang,a['slug'],'structure mismatch')
            doc=BeautifulSoup((ROOT/route(lang,a['slug']).strip('/')/'index.html').read_text(encoding='utf-8'),'html.parser')
            assert doc.h1.text==a['title'] and doc.html['lang']==lang
            assert doc.select_one('link[rel="canonical"]')['href']=='https://worknotetips.com'+route(lang,a['slug'])
            assert len(doc.select('link[hreflang]'))==6
            expected=[b['text'] for s in a['sections'] for b in s['blocks'] if b['type']=='code']
            source=[b['text'] for s in original['sections'] for b in s['blocks'] if b['type']=='code']
            for n,(x,y) in enumerate(zip(source,expected)):
                # Translation can render Korean number words as digits or add
                # :00 to whole hours. Every original numeric token must remain.
                assert not (Counter(re.findall(r'\d+',x))-Counter(re.findall(r'\d+',y))),(lang,a['slug'],'missing source number in block',n)
                assert Counter(re.findall(r'(?<![A-Za-z0-9])[SABF]\d+(?!\d)',x))==Counter(re.findall(r'(?<![A-Za-z0-9])[SABF]\d+(?!\d)',y)),(lang,a['slug'],'source ID drift',n)
            assert len(expected)>=3 and [c.text for c in doc.select('pre code')]==expected
            assert doc.select_one('table') and len(doc.select('.related .article-card'))==7
            assert len(doc.select('button[data-copy]'))==len(expected)
            for button in doc.select('button[data-copy]'): assert doc.find(id=button['data-copy'])
            for script in doc.select('script[type="application/ld+json"]'):
                ld=json.loads(script.string)
                if ld.get('@type')=='TechArticle': assert ld['datePublished']=='2026-09-23'
            pages+=1;blocks+=len(expected)
        base=ROOT/('' if lang=='en' else lang)
        for p,n in [(base/'index.html',82),(base/'category/ai/index.html',51)]:
            doc=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
            assert int(doc.select_one('#result-count').text)==n
    # Independent worked-example calculations, not claims of AI product execution.
    labels={'F1':['visual'],'F2':['location'],'F3':['visual','location'],'F4':['facilitator'],'F5':['return'],'F6':['unclassified']}
    counts={label:sum(label in tags for tags in labels.values()) for label in ['visual','location','facilitator','return','unclassified']}
    assert list(counts.values())==[2,2,1,1,1] and sum(counts.values())==7 and len(labels)==6
    assert sum([2,8,3,2])==15 and sum([4,3,1])==8
    assert Fraction(18,24)*100==75 and Fraction(9,12)*100==75
    brainstorm=next(a for a in baseline if a['slug']=='ai-brainstorm-with-constraints')
    output=next(b['text'] for s in brainstorm['sections'] for b in s['blocks'] if b.get('role')=='output')
    schedules=re.findall(r'^- (\d+)분:',output,re.M)
    assert len(schedules)==20
    assert all(sum(map(int,schedules[i:i+5]))==30 for i in range(0,20,5))
    print(json.dumps({'new_pages':pages,'copyable_blocks':blocks,'translation_structure_and_rendered_examples':'PASS','metadata_and_links':'PASS','feedback_counts_and_time_budgets':'PASS','percentage_denominators':'PASS'},indent=2))

if __name__=='__main__': main()

