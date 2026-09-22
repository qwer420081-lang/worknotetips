"""Check the static pages, routes, locale examples, and deployment invariants."""
import ast
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('en','ko','ja','es','pt-BR')

def main():
    documents = {}
    for path in ROOT.rglob('*.html'):
        if '.git' not in path.parts:
            documents[path] = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    links = 0
    for path, doc in documents.items():
        ids = [tag['id'] for tag in doc.select('[id]')]
        assert len(ids) == len(set(ids)), ('duplicate IDs', path)
        for a in doc.select('a[href]'):
            href = urlsplit(a['href'])
            if href.scheme or href.netloc: continue
            target = ROOT / unquote(href.path).lstrip('/') if href.path.startswith('/') else path.parent / unquote(href.path)
            if not href.path: target = path
            if target.is_dir(): target = target / 'index.html'
            assert target.exists(), ('missing route', path, a['href'])
            if href.fragment and target in documents:
                assert documents[target].find(id=unquote(href.fragment)), ('missing fragment', path, a['href'])
            links += 1
    slugs = []
    for group in ('A','B'):
        slugs.extend(json.loads((ROOT/'_src/verification-patches'/f'vfix_{group}.json').read_text(encoding='utf-8')))
    code_count = 0
    for slug in slugs:
        expected = [c.text for c in documents[ROOT/'articles'/slug/'index.html'].select('pre code')]
        for language in LANGS:
            path = ROOT / ('' if language=='en' else language) / 'articles' / slug / 'index.html'
            doc = documents[path]
            assert [c.text for c in doc.select('pre code')] == expected, ('locale code mismatch', path)
            assert doc.html['lang'] == language
            assert doc.select_one('link[rel="canonical"]')['href'] == 'https://worknotetips.com/' + path.parent.relative_to(ROOT).as_posix() + '/'
            assert len(doc.select('link[hreflang]')) == 6
            assert 'ChatGPT Python tool' in doc.select_one('#verification').text
            assert '2026-09-22' not in doc.select_one('#verification').find('p').text
        for block in documents[ROOT/'articles'/slug/'index.html'].select('.code-block'):
            toolbar = block.select_one('.code-toolbar span')
            if toolbar and toolbar.text.lower() == 'python':
                ast.parse(block.code.text); code_count += 1
    assert (ROOT/'CNAME').read_text().strip() == 'worknotetips.com'
    assert (ROOT/'.nojekyll').exists()
    assert (ROOT/'googled1237ebe1fdf792c.html').exists()
    assert documents[ROOT/'index.html'].select_one('meta[name="google-site-verification"]')
    print(json.dumps({'html_pages':len(documents), 'internal_links_checked':links, 'updated_locale_pages':len(slugs)*5, 'python_blocks_parsed':code_count, 'locale_code_consistency':'PASS', 'domain_and_google_verification':'PASS'}, indent=2))

if __name__ == '__main__': main()
