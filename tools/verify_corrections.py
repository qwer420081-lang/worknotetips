"""Execute the five corrected examples in temporary folders. Requires Pillow, bs4."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def page(slug):
    return BeautifulSoup((ROOT / 'articles' / slug / 'index.html').read_text(encoding='utf-8'), 'html.parser')

def run(code, directory, success=True):
    p = subprocess.run([sys.executable, '-c', code], cwd=directory, capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    assert (p.returncode == 0) == success, p.stdout + p.stderr
    return p.stdout

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    results = {}
    with tempfile.TemporaryDirectory(prefix='worknote-qa-') as temp:
        base = Path(temp)
        s = page('batch-image-resize')
        d = base / 'images'; d.mkdir()
        run(s.select_one('#code-1-1').text, d)
        sources = list(d.rglob('*.png'))
        before = {p: digest(p) for p in sources}
        output = run(s.select_one('#code-3-1').text, d)
        assert sum(Image.open(p).width * Image.open(p).height for p in sources) == 1340000
        created = [p for p in d.rglob('*.png') if p not in sources]
        assert {p.name: Image.open(p).size for p in created} == {'landscape.png': (300,225), 'portrait.png': (225,300), 'small.png': (200,100), 'wide.png': (300,75)}
        assert all(digest(p) == h for p,h in before.items())
        run(s.select_one('#code-3-1').text, d, False)
        results['batch-image-resize'] = '4 dimensions, 1,340,000 source pixels, source hashes and overwrite refusal passed'

        s = page('unit-conversion-check'); d = base / 'units'; d.mkdir()
        source = d / 'unit_test_data.csv'; source.write_text(s.select_one('#code-1-1').text, encoding='utf-8')
        before = digest(source)
        run(s.select_one('#code-3-1').text, d)
        actual = (d / 'outputs/unit_conversion_result/converted_test_data.csv').read_text(encoding='utf-8').strip()
        assert actual == s.select_one('#code-4-1').text.strip(), 'Published expected CSV differs from execution'
        assert digest(source) == before
        run(s.select_one('#code-3-1').text, d, False)
        results['unit-conversion-check'] = 'All 5 exact CSV rows, source hash and overwrite refusal passed'

        s = page('ai-email-draft-check'); d = base / 'email'; d.mkdir()
        paragraph = s.select_one('#ask-ai-for-draft').find_all('p', recursive=False)[1].text
        start = paragraph.index('Hello Mina Park')
        draft = paragraph[start:paragraph.index('Best regards.', start) + len('Best regards.')]
        source = d / 'draft_email.txt'; source.write_text(draft, encoding='utf-8'); before = digest(source)
        code = s.select_one('#code-4-1').text
        run(code, d)
        report = (d / 'outputs/email_check_report.txt').read_text(encoding='utf-8')
        assert 'CHECK:' not in report, report
        assert report.count('PASS:') == 8, report
        assert digest(source) == before
        run(code, d, False)
        results['ai-email-draft-check'] = 'Published draft: 7 required details and risky-phrase check passed; no overwrite'

        s = page('ai-translation-check'); code = s.select_one('#code-5-1').text
        for lang, translation in [('ko', '12개 샘플. Bolt A를 35 N·m로 조입니다. 80 °C를 넘지 마세요. 보고 기한 October 14, 2026. Mina Park. Alpha-X.'), ('ja', '12個のサンプル。Bolt Aを35 N·mで締めます。80 °Cを超えないでください。期限October 14, 2026。Mina Park。Alpha-X。'), ('changed', '13 samples. 35 N·m. 80 °C. October 14, 2026. Mina Park. Alpha-X.')]:
            d = base / lang; d.mkdir()
            (d / 'source.txt').write_text('Prepare 12 samples. Tighten Bolt A to 35 N·m. Do not exceed 80 °C. Send the report by October 14, 2026 to Mina Park. Use Alpha-X.', encoding='utf-8')
            (d / 'translation.txt').write_text(translation, encoding='utf-8')
            before = {p: digest(p) for p in d.glob('*.txt')}
            run(code, d)
            report = (d / 'outputs/translation_check_report.txt').read_text(encoding='utf-8')
            assert ('PASS: number sequence matches' in report) == (lang != 'changed'), report
            assert all(digest(p) == h for p,h in before.items())
            run(code, d, False)
        results['ai-translation-check'] = 'Korean/Japanese adjacent digits pass, changed quantity detected; source hashes and no overwrite passed'

        s = page('ai-mask-personal-data'); d = base / 'mask'; d.mkdir()
        source = d / 'message.txt'; source.write_text(s.select_one('#code-0-2').text, encoding='utf-8'); before = digest(source)
        assert source.read_text(encoding='utf-8').count('Alice Kim') == 1
        code = s.select_one('#code-3-1').text; run(code, d)
        masked = (d / 'outputs/message_masked.txt').read_text(encoding='utf-8')
        assert masked.count('[NAME_1]') == 1 and 'A. Kim' in masked and 'Alice' in masked
        with (d / 'outputs/replacements.csv').open(encoding='utf-8', newline='') as stream:
            assert len(list(csv.DictReader(stream))) == 6
        assert digest(source) == before
        run(code, d, False)
        results['ai-mask-personal-data'] = 'Alice Kim once, 6 unique replacements, partial names intentionally unchanged; no overwrite'
    print(json.dumps({'python':sys.version.split()[0], 'results':results}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
