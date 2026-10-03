"""Publish reviewed GPT Chat drafts and retain the existing reader paths."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from build_beginner_articles import main as build, LANGS, route
from build_reader_paths import build as reader_paths

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-10-03'
BATCH = 'ai-review-batch'
REFERENCE = 'https://www.anthropic.com/news/prompting-long-context'

def main():
    privacy = {lang: (ROOT / ('' if lang == 'en' else lang) / 'privacy/index.html').read_bytes() for lang in LANGS}
    build(BATCH, DATE)
    for lang in LANGS:
        articles = json.loads((ROOT / '_src' / BATCH / f'{lang}.json').read_text(encoding='utf-8'))['articles']
        for article in articles:
            p = ROOT / route(lang, article['slug']).strip('/') / 'index.html'
            doc = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
            for script in doc.select('script[type="application/ld+json"]'):
                data = json.loads(script.string)
                if data.get('@type') == 'TechArticle':
                    data['datePublished'] = DATE
                    script.string = json.dumps(data, ensure_ascii=False)
            if article['slug'] == 'ai-long-document-chunks':
                # Link the primary source explicitly rather than leaving a bare URL.
                section = doc.new_tag('section', id='references')
                h = doc.new_tag('h2'); h.string = {'en':'Source for the background','ko':'원리 설명의 참고 자료','ja':'背景説明の参考資料','es':'Fuente de la explicación','pt-BR':'Fonte da explicação'}[lang]
                section.append(h)
                a = doc.new_tag('a', href=REFERENCE)
                a.string = "Anthropic — Prompt engineering for Claude’s long context window (2023)"
                section.append(a); doc.select_one('.reading-content').append(section)
            related = doc.select_one('.related .article-grid')
            for slug in ['ai-document-qa-citations', 'ai-summary-source-check']:
                source = BeautifulSoup((ROOT / route(lang, slug).strip('/') / 'index.html').read_text(encoding='utf-8'), 'html.parser')
                card = doc.new_tag('article', attrs={'class':'article-card'})
                h = doc.new_tag('h3'); a = doc.new_tag('a', href=route(lang, slug)); a.string = source.h1.get_text(); h.append(a); card.append(h); related.append(card)
            p.write_text(str(doc), encoding='utf-8')
    reader_paths()
    for lang, data in privacy.items():
        (ROOT / ('' if lang == 'en' else lang) / 'privacy/index.html').write_bytes(data)
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    xhtml = 'http://www.w3.org/1999/xhtml'
    ET.register_namespace('', ns); ET.register_namespace('xhtml', xhtml)
    p = ROOT / 'sitemap.xml'; tree = ET.parse(p)
    incoming = {a['slug'] for a in articles}
    updated = {'https://worknotetips.com' + ('/' if lang == 'en' else '/' + lang + '/') + suffix for lang in LANGS for suffix in ['', 'category/ai/']}
    for item in tree.getroot():
        loc = item.find('{' + ns + '}loc').text
        slug = loc.rstrip('/').split('/')[-1]
        if loc in updated:
            item.find('{' + ns + '}lastmod').text = DATE
        if slug in incoming:
            for child in list(item.findall('{' + xhtml + '}link')): item.remove(child)
            for lang in [*LANGS, 'x-default']:
                ET.SubElement(item, '{' + xhtml + '}link', rel='alternate', hreflang=lang, href='https://worknotetips.com' + route('en' if lang == 'x-default' else lang, slug))
    tree.write(p, encoding='utf-8', xml_declaration=True)
    print('Published two topics in five languages; reader paths preserved.')

if __name__ == '__main__': main()
