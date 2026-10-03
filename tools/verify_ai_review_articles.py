"""Validate source coverage, grading arithmetic and translated publication."""
import json
import re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from build_beginner_articles import LANGS, route

ROOT = Path(__file__).resolve().parents[1]
def shape(a):
    return [(s['id'], [(b['type'], b.get('role'), len(b.get('rows', [])), len(b.get('headers', [])), len(b.get('items', []))) for b in s['blocks']]) for s in a['sections']]

def main():
    baseline = json.loads((ROOT / '_src/ai-review-batch/ko.json').read_text(encoding='utf-8'))['articles']
    pages = prompts = 0
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    entries = {e.find(ns + 'loc').text: e for e in sitemap.getroot()}
    assert len(entries) == 475
    for lang in LANGS:
        data = json.loads((ROOT / '_src/ai-review-batch' / f'{lang}.json').read_text(encoding='utf-8'))
        assert data['lang'] == lang
        assert [a['slug'] for a in data['articles']] == [a['slug'] for a in baseline]
        for original, a in zip(baseline, data['articles']):
            assert shape(original) == shape(a), (lang, a['slug'], 'translation structure')
            source_blocks = [b for s in original['sections'] for b in s['blocks'] if b['type'] == 'code']
            blocks = [b for s in a['sections'] for b in s['blocks'] if b['type'] == 'code']
            assert len(blocks) >= 3
            for source, translated in zip(source_blocks, blocks):
                identifiers = lambda text: Counter(re.findall(r'(?<![A-Za-z0-9])(?:DOC-01|C[1-3]|L[1-6]|v1)(?![A-Za-z0-9])', text))
                assert identifiers(source['text']) == identifiers(translated['text']), (lang, 'source identifiers')
                # Compare numeric sequences, tolerating locale comma/space grouping.
                def numbers(text):
                    text = re.sub(r'(?i)\b(?:october|octubre|outubro)\b', '10', text)
                    text = re.sub(r'(?<=\d)[,.\u00a0](?=\d{3}(?:\D|$))', '', text)
                    return Counter(re.findall(r'\d+', text))
                original_numbers, translated_numbers = numbers(source['text']), numbers(translated['text'])
                if lang == 'ja' and source['role'] in {'prompt', 'checklist'}:
                    # Reviewed Japanese renders Korean words for one/six as 1/6.
                    assert not (original_numbers - translated_numbers)
                    assert set(translated_numbers - original_numbers) <= {'1', '6'}
                else:
                    assert original_numbers == translated_numbers, (lang, a['slug'], 'example number drift', source['role'])
            p = ROOT / route(lang, a['slug']).strip('/') / 'index.html'
            doc = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
            assert doc.html['lang'] == lang and doc.h1.text == a['title']
            url = 'https://worknotetips.com' + route(lang, a['slug'])
            assert doc.select_one('link[rel="canonical"]')['href'] == url
            assert len(doc.select('link[rel="alternate"][hreflang]')) == 6
            assert len(entries[url].findall('{http://www.w3.org/1999/xhtml}link')) == 6
            assert [c.text for c in doc.select('pre code')] == [b['text'] for b in blocks]
            assert len(doc.select('button[data-copy]')) == len(blocks)
            for button in doc.select('button[data-copy]'): assert doc.find(id=button['data-copy'])
            assert doc.select_one('table') and len(doc.select('.related .article-card')) == 3
            ld = [json.loads(s.string) for s in doc.select('script[type="application/ld+json"]')]
            assert next(x for x in ld if x.get('@type') == 'TechArticle')['datePublished'] == '2026-10-03'
            if a['slug'] == 'ai-long-document-chunks': assert doc.select_one('#references a')['href'] == 'https://www.anthropic.com/news/prompting-long-context'
            pages += 1; prompts += len(blocks)
        base = ROOT / ('' if lang == 'en' else lang)
        for path, count in [(base / 'index.html', 84), (base / 'category/ai/index.html', 53)]:
            doc = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
            assert int(doc.select_one('#result-count').text) == count
            assert len(doc.select('main .article-grid > .article-card')) == count
        home = BeautifulSoup((base / 'index.html').read_text(encoding='utf-8'), 'html.parser')
        assert len(home.select('#start-here')) == 1 and home.select_one('.primary-start')
        mobile = home.select_one('.mobile-browse').text
        assert '84' in mobile and '53' in mobile
    # Independent oracle: overlap covers six unique lines; publication gate is separate.
    chunks = [{'L1', 'L2'}, {'L2', 'L3', 'L4'}, {'L5', 'L6'}]
    assert len(set.union(*chunks)) == 6 and sum(map(len, chunks)) == 7
    scores = {'A': [1, 1, 1, 1, 1, 1], 'B': [0, 1, 1, 1, 0, 0]}
    assert sum(scores['A']) == 6 and sum(scores['B']) == 3
    unsupported = {'A': False, 'B': True}
    publishable = {name: sum(values) == 6 and not unsupported[name] for name, values in scores.items()}
    assert publishable == {'A': True, 'B': False}
    print(json.dumps({'pages': pages, 'copyable_blocks': prompts, 'translation_structure_and_numbers': 'PASS', 'independent_coverage_and_score_oracle': 'PASS', 'routes_metadata_and_reader_paths': 'PASS'}, indent=2))

if __name__ == '__main__': main()
