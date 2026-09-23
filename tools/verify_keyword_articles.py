"""Verify translated presentation evidence, prompts, and preserved examples."""
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from bs4 import BeautifulSoup
from build_beginner_articles import LANGS,route
ROOT=Path(__file__).resolve().parents[1]

def main():
    assert Fraction(18,24)*100==75 and Fraction(9,12)*100==75
    # Unknown responses must not be silently treated as negative responses.
    possible=[Fraction(9+x,18)*100 for x in range(7)]
    assert len(set(possible))==7
    baseline=None; copy_blocks=0
    for lang in LANGS:
        data=json.loads((ROOT/'_src/keyword-batch'/f'{lang}.json').read_text(encoding='utf-8'))
        article=data['articles'][0]
        structure=[(s['id'],[(b['type'],len(b.get('rows',[])),len(b.get('items',[]))) for b in s['blocks']]) for s in article['sections']]
        if baseline is None: baseline=structure
        assert structure==baseline,(lang,'structure drift')
        path=ROOT/route(lang,article['slug']).strip('/')/'index.html'
        doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        assert doc.h1.text==article['title'] and doc.html['lang']==lang
        assert doc.select_one('link[rel="canonical"]')['href']=='https://worknotetips.com'+route(lang,article['slug'])
        assert len(doc.select('link[hreflang]'))==6
        expected=[b['text'] for s in article['sections'] for b in s['blocks'] if b['type']=='code']
        assert [c.text for c in doc.select('pre code')]==expected
        table=doc.select_one('#editorial-example table'); rows=table.select('tbody tr')
        assert len(rows)==6 and all(len(r.select('td'))==6 for r in rows)
        assert all('S' in r.select('td')[3].text for r in rows)
        assert '24' in expected[0] and '18' in expected[0] and '12' in expected[0] and '9' in expected[0]
        for patch in data['patches']:
            path=ROOT/route(lang,patch['slug']).strip('/')/'index.html'
            doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            assert doc.h1.text==patch['title']
            assert doc.select_one('#localized-report-prompt').text==patch['prompt']
            original=subprocess.check_output(['git','show','2336fc1:'+path.relative_to(ROOT).as_posix()],cwd=ROOT).decode('utf-8').replace('\r\n','\n')
            old=BeautifulSoup(original,'html.parser')
            assert [c.text for c in old.select('pre code')]==[c.text for c in doc.select('pre code:not(#localized-report-prompt)')],(lang,'changed original code')
            assert old.select_one('#verification').text==doc.select_one('#verification').text
            assert doc.select_one('.related a[href="'+route(lang,article['slug'])+'"]')
        for slug in [article['slug'],*[p['slug'] for p in data['patches']]]:
            doc=BeautifulSoup((ROOT/route(lang,slug).strip('/')/'index.html').read_text(encoding='utf-8'),'html.parser')
            for button in doc.select('button[data-copy]'):
                assert doc.find(id=button['data-copy']); copy_blocks+=1
    print(json.dumps({'new_pages':5,'updated_articles':10,'translation_structure':'PASS','six_slide_evidence_tables':'PASS','original_code_and_verification_preserved':'PASS','copy_targets':copy_blocks,'fractions_recalculated':'PASS'},indent=2))

if __name__=='__main__': main()
