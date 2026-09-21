"""Apply reviewed verification JSON to the static site without rebuilding its shell.

Usage: python tools/apply_verification_patches.py DIRECTORY
Requires beautifulsoup4. English inputs: vfix_A.json, vfix_B.json.
Translations: objects with file, lang, data keys (A/B x ko/ja/es/pt-BR).
"""
import copy
import html
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('en', 'ko', 'ja', 'es', 'pt-BR')

def replace_section(document, ident, transform):
    pattern = re.compile(r'<section\b[^>]*\bid="' + re.escape(ident) + r'"[^>]*>.*?</section>', re.S)
    matches = list(pattern.finditer(document))
    assert len(matches) == 1, ident
    match = matches[0]
    soup = BeautifulSoup(match.group(), 'html.parser')
    section = soup.section
    transform(soup, section)
    return document[:match.start()] + str(section) + document[match.end():]

def set_fix(soup, section, fix):
    blocks = [x for x in section.find_all(recursive=False) if x.name != 'h2']
    block = blocks[fix['block_index']]
    value = fix['new_value']
    if isinstance(value, str):
        value = value.replace('October 9. Please', 'October 9, 2026. Please')
    if fix['type'] == 'table':
        tbody = block.find('tbody'); assert tbody
        tbody.clear()
        for row in value:
            tr = soup.new_tag('tr')
            for cell in row:
                td = soup.new_tag('td'); td.string = str(cell); tr.append(td)
            tbody.append(tr)
    elif fix['type'] == 'code':
        code = block.find('code'); assert code
        code.clear(); code.append(value)
    else:
        assert block.name == 'p', (fix, block.name)
        block.clear(); block.append(value)

def set_verification(soup, section, verification):
    title = copy.copy(section.h2)
    limit_title = section.select_one('.verification-limits strong').text
    section.clear(); section.append(title)
    p = soup.new_tag('p'); p.string = verification['env']; section.append(p)
    def listing(items):
        ul = soup.new_tag('ul')
        for item in items:
            li = soup.new_tag('li'); li.string = item; ul.append(li)
        return ul
    section.append(listing(verification['items']))
    limits = soup.new_tag('div', attrs={'class': 'verification-limits'})
    strong = soup.new_tag('strong'); strong.string = limit_title; limits.append(strong)
    limits.append(listing(verification['limits'])); section.append(limits)

def main():
    directory = Path(sys.argv[1])
    data = {lang:{} for lang in LANGS}
    for path in directory.rglob('*.json'):
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(value, dict) and value.get('lang') in LANGS and 'data' in value:
            language = value['lang']; batch = value['data']
        elif path.stem in ('vfix_A', 'vfix_B'):
            language = 'en'; batch = value.get('data', value)
        else:
            continue
        assert not (set(data[language]) & set(batch)), path
        data[language].update(batch)
    assert all(len(v) == 35 for v in data.values()), {k:len(v) for k,v in data.items()}
    assert all(set(v) == set(data['en']) for v in data.values())
    changed = []
    for language, articles in data.items():
        for slug, patch in articles.items():
            verification = copy.deepcopy(patch['verification'])
            # The imported record contains a future date; do not publish it as a verified timestamp.
            verification['env'] = re.sub(r'^2026-09-22\s*·\s*', '', verification['env'])
            path = ROOT / ('' if language == 'en' else language) / 'articles' / slug / 'index.html'
            document = path.read_text(encoding='utf-8')
            for fix in patch.get('text_fixes', []):
                document = replace_section(document, fix['section_id'], lambda soup, section: set_fix(soup, section, fix))
            document = replace_section(document, 'verification', lambda soup, section: set_verification(soup, section, verification))
            if slug == 'ai-translation-check':
                old = r'\b\d+(?:\.\d+)?\b'; new = r'(?<!\d)\d+(?:\.\d+)?(?!\d)'
                if old in document:
                    assert document.count(old) == 1
                    document = document.replace(old, html.escape(new, quote=True))
                else:
                    assert html.escape(new, quote=True) in document
            path.write_text(document, encoding='utf-8', newline='')
            changed.append(str(path.relative_to(ROOT)))
            if language == 'en':
                source_path = ROOT / '_src' / f'{slug}.json'
                source = json.loads(source_path.read_text(encoding='utf-8'))
                source['verification'] = verification
                for fix in patch.get('text_fixes', []):
                    section = next(s for s in source['sections'] if s['id'] == fix['section_id'])
                    value = fix['new_value']
                    if isinstance(value, str): value = value.replace('October 9. Please', 'October 9, 2026. Please')
                    section['blocks'][fix['block_index']][fix['field']] = value
                # Hydrate executable examples that the original translation-only source omitted.
                rendered = BeautifulSoup(document, 'html.parser')
                for si, section in enumerate(source['sections']):
                    for bi, block in enumerate(section['blocks']):
                        if block['type'] == 'code':
                            code = rendered.find(id=f'code-{si}-{bi}')
                            if code: block['text'] = code.text
                source_path.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Updated {len(changed)} pages and 35 English source files.')

if __name__ == '__main__':
    main()
