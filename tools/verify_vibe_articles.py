"""Check the Claude Code vibe-coding series: structure, rendering, shared code and worked outputs."""
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup
from build_beginner_articles import LANGS, route

ROOT = Path(__file__).resolve().parents[1]
HANGUL = re.compile('[가-힣]')
GOOD = "date,category,amount\n2026-09-01,food,12000\n2026-09-03,transport,1450\n2026-09-03,food,8500\n2026-09-10,supplies,3200\n2026-09-15,transport,1450\n2026-10-02,food,9800\n"
BAD = GOOD.replace('transport,1450\n2026-09-03', 'transport,"1,450"\n2026-09-03', 1)
ABC = "date,category,amount\n2026-09-01,food,12000\n2026-09-03,transport,abc\n"
MONTHLY = "2026-09 = 26600\n2026-10 = 9800\n"
BY_CATEGORY = "2026-09 = 26600\n  food = 20500\n  supplies = 3200\n  transport = 2900\n2026-10 = 9800\n  food = 9800\n"

def run(code, csv_text, *args):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); (tmp / 's.py').write_text(code, encoding='utf-8'); (tmp / 'e.csv').write_text(csv_text, encoding='utf-8')
        return subprocess.run([sys.executable, 's.py', 'e.csv', *args], cwd=tmp, capture_output=True, text=True, encoding='utf-8')

def main():
    source = ROOT / '_src/vibe-batch'
    original = json.loads((source / 'ko.json').read_text(encoding='utf-8'))['articles']
    assert len(original) == 8
    pages = blocks = 0
    for lang in LANGS:
        data = json.loads((source / f'{lang}.json').read_text(encoding='utf-8'))
        assert data['lang'] == lang
        articles = data['articles']
        assert [a['slug'] for a in articles] == [a['slug'] for a in original]
        for base, a in zip(original, articles):
            assert [s['id'] for s in a['sections']] == [s['id'] for s in base['sections']]
            for bs, s in zip(base['sections'], a['sections']):
                assert [b['type'] for b in bs['blocks']] == [b['type'] for b in s['blocks']], (lang, a['slug'], s['id'])
                for b, t in zip(bs['blocks'], s['blocks']):
                    if b['type'] == 'table': assert (len(b['headers']), len(b['rows'])) == (len(t['headers']), len(t['rows']))
                    if b['type'] == 'code':
                        if not HANGUL.search(b['text']): assert b['text'] == t['text'], (lang, a['slug'], s['id'], 'shared code changed')
                        assert b['text'].startswith('[') == t['text'].startswith('['), (lang, a['slug'], 'editorial label')
            if lang != 'ko': assert not HANGUL.search(json.dumps(a, ensure_ascii=False)), (lang, a['slug'], 'untranslated Korean')
            doc = BeautifulSoup((ROOT / route(lang, a['slug']).strip('/') / 'index.html').read_text(encoding='utf-8'), 'html.parser')
            expected = [b['text'] for s in a['sections'] for b in s['blocks'] if b['type'] == 'code']
            assert [c.get_text() for c in doc.select('pre code')] == expected
            assert doc.h1.text == a['title'] and doc.html['lang'] == lang and len(doc.select('link[hreflang]')) == 6
            assert doc.select_one('link[rel="canonical"]')['href'] == 'https://worknotetips.com' + route(lang, a['slug'])
            pages += 1; blocks += len(expected)
    python = [b['text'] for a in original for s in a['sections'] for b in s['blocks'] if b['type'] == 'code' and 'import csv' in b['text']]
    assert len(python) == 4
    for code in python: ast.parse(code)
    first, category, buggy, fixed = python
    assert run(first, GOOD).stdout == MONTHLY
    assert run(category, GOOD).stdout == MONTHLY and run(category, GOOD, '--by-category').stdout == BY_CATEGORY
    assert run(category, GOOD, '--wrong').returncode == 2
    r = run(buggy, BAD); assert r.returncode == 1 and r.stderr.strip().endswith("ValueError: invalid literal for int() with base 10: '1,450'")
    assert run(fixed, BAD).stdout == MONTHLY and run(fixed, GOOD).stdout == MONTHLY
    r = run(fixed, ABC); assert r.stderr.strip().endswith("ValueError: line 3: amount must be an integer, got 'abc'")
    assert 12000 + 1450 + 8500 + 3200 + 1450 == 26600 and 12000 + 8500 == 20500 and 1450 * 2 == 2900
    print(json.dumps({'series_pages': pages, 'copyable_blocks': blocks, 'structure_and_shared_code': 'PASS', 'python_outputs_and_errors': 'PASS', 'python': sys.version.split()[0]}, indent=2))

if __name__ == '__main__': main()
