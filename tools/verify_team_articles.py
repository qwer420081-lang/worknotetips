"""Check the team-collaboration AI series: structure, translated facts, traceable outputs and rendering."""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from build_beginner_articles import LANGS, route

ROOT = Path(__file__).resolve().parents[1]
HANGUL = re.compile('[가-힣]')
NAMES = {'ko': ['민서', '준호', '서연', '도윤'], 'ja': ['ミンソ', 'ジュノ', 'ソヨン', 'ドユン']}
for lang in ('en', 'es', 'pt-BR'): NAMES[lang] = ['Minseo', 'Junho', 'Seoyeon', 'Doyun']
FACTS = ['2026-11-14', '14:00', '16:00', '2026-10-24', '2026-10-28', '2026-10-30', '2026-10-23']

def tokens(text):
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
    times = re.findall(r'(?<!\d)\d{1,2}:\d{2}(?!\d)', text)
    rest = re.sub(r'\d{4}-\d{2}-\d{2}|(?<!\d)\d{1,2}:\d{2}(?!\d)', ' ', text)
    return sorted(dates + times + re.findall(r'\d+', rest))

def main():
    source = ROOT / '_src/team-batch'
    original = json.loads((source / 'ko.json').read_text(encoding='utf-8'))['articles']
    assert len(original) == 8
    pages = blocks = traced = 0
    for lang in LANGS:
        data = json.loads((source / f'{lang}.json').read_text(encoding='utf-8'))
        assert data['lang'] == lang
        articles = data['articles']
        assert [a['slug'] for a in articles] == [a['slug'] for a in original]
        for index, (base, a) in enumerate(zip(original, articles)):
            assert [s['id'] for s in a['sections']] == [s['id'] for s in base['sections']]
            codes = []
            for bs, s in zip(base['sections'], a['sections']):
                assert [(b['type'], b.get('role')) for b in bs['blocks']] == [(b['type'], b.get('role')) for b in s['blocks']], (lang, a['slug'], s['id'])
                for b, t in zip(bs['blocks'], s['blocks']):
                    if b['type'] == 'table':
                        assert (len(b['headers']), len(b['rows'])) == (len(t['headers']), len(t['rows']))
                        assert all(len(r) == len(t['headers']) for r in t['rows'])
                        assert [tokens(' | '.join(r)) for r in b['rows']] == [tokens(' | '.join(r)) for r in t['rows']], (lang, a['slug'], 'table numbers')
                    if b['type'] == 'code':
                        assert len(b['text'].splitlines()) == len(t['text'].splitlines()), (lang, a['slug'], s['id'], 'line count')
                        assert tokens(b['text']) == tokens(t['text']), (lang, a['slug'], s['id'], 'code numbers')
                        assert t['text'].startswith('[') == (t['role'] in ('output', 'bad_output')), (lang, a['slug'], 'example label')
                        codes.append(t)
            roles = {c['role'] for c in codes}
            assert {'input', 'prompt', 'output', 'bad_output'} <= roles, (lang, a['slug'])
            source_text = ' '.join(c['text'] for c in codes if c['role'] == 'input')
            for c in codes:
                if c['role'] == 'output':
                    assert set(tokens(c['text'])) <= set(tokens(source_text)), (lang, a['slug'], set(tokens(c['text'])) - set(tokens(source_text)))
                    for name in NAMES[lang]:
                        if name in c['text']: assert name in source_text, (lang, a['slug'], name)
                    traced += 1
            flat = json.dumps(a, ensure_ascii=False)
            assert all(fact in flat for fact in ('2026-11-14', '14:00')), (lang, a['slug'])
            if lang != 'ko': assert not HANGUL.search(flat), (lang, a['slug'], 'untranslated Korean')
            assert not re.search(r'\d+\s*%', flat), (lang, a['slug'], 'percentage claim')
            following = articles[(index + 1) % len(articles)]['title']
            assert following in a['sections'][-1]['blocks'][-1]['text'], (lang, a['slug'], 'next article title')
            path = ROOT / route(lang, a['slug']).strip('/') / 'index.html'
            doc = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
            expected = [c['text'] for c in codes]
            assert [x.get_text() for x in doc.select('pre code')] == expected
            assert len(doc.select('[data-copy]')) == len(expected) and all(doc.find(id=b['data-copy']) for b in doc.select('[data-copy]'))
            assert doc.h1.text == a['title'] and doc.html['lang'] == lang
            assert doc.select_one('link[rel="canonical"]')['href'] == 'https://worknotetips.com' + route(lang, a['slug'])
            links = doc.select('link[hreflang]'); assert len(links) == 6 and all(a['slug'] in l['href'] for l in links)
            related = {x['href'] for x in doc.select('.related a[href]')}
            assert {route(lang, o['slug']) for o in articles if o['slug'] != a['slug']} <= related, (lang, a['slug'], 'related links')
            pages += 1; blocks += len(expected)
    print(json.dumps({'series_pages': pages, 'copyable_blocks': blocks, 'traced_example_outputs': traced, 'structure_numbers_and_labels': 'PASS', 'outputs_use_only_input_facts': 'PASS', 'rendering_canonical_hreflang_related': 'PASS'}, indent=2))

if __name__ == '__main__': main()
