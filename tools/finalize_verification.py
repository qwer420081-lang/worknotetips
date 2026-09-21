"""Apply editorial corrections and distinguish imported records from local rechecks."""
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup
from apply_verification_patches import ROOT, LANGS, replace_section

COPY = {
 'en': ['Example files included', 'Example code included', 'The boundary tests and execution results are recorded in the verification section below.', 'Six files require hashing: the two empty files and all four three-byte files. The four-byte file has no size peer and is skipped. The execution matched the expected console output.', 'The execution matched the expected output. Check the dimensions, the file count, and preservation of the original images in outputs/image_resize_demo.', 'Local recheck on 2026-09-21 with Python 3.12.14: the corrected example passed; source preservation and overwrite protection also passed.', 'The corrected email draft contains Mina Park, Example Parts, and both complete dates (October 7, 2026 and October 9, 2026). All seven required-detail checks and the risky-phrase check passed.'],
 'ko': ['예제 파일 포함', '예제 코드 포함', '경계 조건 테스트와 실행 결과는 아래 실행·검증 기록에서 확인할 수 있습니다.', '해시 계산 대상은 빈 파일 2개와 3바이트 파일 4개로 총 6개입니다. 4바이트 파일은 크기가 같은 다른 파일이 없어 건너뜁니다. 실제 콘솔 출력은 예상과 일치했습니다.', '실제 실행 결과가 예상 출력과 일치했습니다. 이미지 크기와 파일 수, outputs/image_resize_demo의 원본 보존 여부를 확인하세요.', '2026-09-21 Python 3.12.14로 로컬 재검증: 수정된 예제가 통과했고 원본 보존과 덮어쓰기 방지도 확인했습니다.', '수정된 이메일 초안에는 Mina Park, Example Parts와 연도를 포함한 두 날짜(October 7, 2026 및 October 9, 2026)가 있습니다. 필수 정보 7개와 위험한 약속 표현 검사가 모두 통과했습니다.'],
 'ja': ['サンプルファイル付き', 'サンプルコード付き', '境界条件のテストと実行結果は、以下の実行・検証記録で確認できます。', 'ハッシュ計算の対象は空のファイル2個と3バイトのファイル4個、合計6個です。4バイトのファイルには同じサイズの相手がないためスキップされます。実際のコンソール出力は想定と一致しました。', '実行結果は想定出力と一致しました。画像サイズ、ファイル数、outputs/image_resize_demo内の元画像が保持されていることを確認してください。', '2026-09-21にPython 3.12.14でローカル再検証しました。修正済みの例、元ファイルの保持、上書き防止の確認はすべて合格しました。', '修正したメールにはMina Park、Example Parts、年を含む両方の日付（October 7, 2026とOctober 9, 2026）が含まれます。必須情報7件と危険な約束表現のチェックがすべて合格しました。'],
 'es': ['Incluye archivos de ejemplo', 'Incluye código de ejemplo', 'Las pruebas de casos límite y sus resultados figuran en la sección de verificación que aparece más abajo.', 'Se calculan hashes de seis archivos: los dos vacíos y los cuatro de tres bytes. El archivo de cuatro bytes se omite porque no tiene otro del mismo tamaño. La ejecución coincidió con la salida de consola esperada.', 'La ejecución coincidió con la salida esperada. Compruebe las dimensiones, el número de archivos y la conservación de los originales en outputs/image_resize_demo.', 'Verificación local del 2026-09-21 con Python 3.12.14: el ejemplo corregido pasó, al igual que la conservación de los originales y la protección contra sobrescritura.', 'El borrador corregido contiene Mina Park, Example Parts y ambas fechas completas (October 7, 2026 y October 9, 2026). Pasaron las siete comprobaciones de datos obligatorios y la comprobación de promesas arriesgadas.'],
 'pt-BR': ['Inclui arquivos de exemplo', 'Inclui código de exemplo', 'Os testes de casos limite e os resultados de execução estão registrados na seção de verificação abaixo.', 'São calculados hashes de seis arquivos: os dois vazios e os quatro de três bytes. O arquivo de quatro bytes é ignorado porque não há outro do mesmo tamanho. A execução correspondeu à saída esperada no console.', 'A execução correspondeu à saída esperada. Confira as dimensões, a quantidade de arquivos e a preservação dos originais em outputs/image_resize_demo.', 'Verificação local em 2026-09-21 com Python 3.12.14: o exemplo corrigido passou, assim como a preservação dos originais e a proteção contra sobrescrita.', 'O rascunho corrigido contém Mina Park, Example Parts e as duas datas completas (October 7, 2026 e October 9, 2026). As sete verificações de dados obrigatórios e a verificação de promessas arriscadas passaram.'],
}
RECHECKED = {'batch-image-resize', 'unit-conversion-check', 'ai-email-draft-check', 'ai-translation-check', 'ai-mask-personal-data'}
EDITS = {'split-large-csv': ('checks-before-use', -1, 2), 'find-duplicate-files': ('expected-review-report', -1, 3), 'batch-image-resize': ('expected-result', -1, 4)}
BOUNDARIES = {
 'en': 'Test in separate folders: 6 records produce two parts of 3; a header-only input produces no parts; a completely empty file is rejected. ',
 'ko': '별도 폴더에서 테스트하세요. 레코드 6개는 3개씩 두 파일로 나뉘고, 헤더만 있으면 분할 파일이 생성되지 않으며, 완전히 빈 파일은 거부됩니다. ',
 'ja': '別々のフォルダでテストしてください。6レコードは3件ずつ2ファイルに分割され、ヘッダーのみの場合は分割ファイルを作成せず、完全に空のファイルは拒否されます。 ',
 'es': 'Pruebe en carpetas separadas: 6 registros producen dos partes de 3; una entrada con solo encabezado no produce partes; un archivo totalmente vacío se rechaza. ',
 'pt-BR': 'Teste em pastas separadas: 6 registros produzem duas partes de 3; uma entrada apenas com cabeçalho não produz partes; um arquivo totalmente vazio é rejeitado. ',
}
HASH_TABLE = {
 'en': 'The report has five data rows plus its header. Groups are ordered by size and digest, with sorted paths in each group. The table below omits the SHA-256 column for readability; the generated CSV includes it and the values were checked during execution.',
 'ko': '보고서는 헤더와 데이터 5행으로 구성됩니다. 그룹은 크기와 해시 순으로, 각 그룹의 경로는 정렬되어 있습니다. 아래 표에서는 읽기 쉽도록 SHA-256 열을 생략했지만 생성된 CSV에는 포함되며 실행 시 값을 확인했습니다.',
 'ja': 'レポートはヘッダーと5行のデータで構成されます。グループはサイズとハッシュ順、各グループ内のパスも並べ替えられています。読みやすさのため下表ではSHA-256列を省略していますが、生成されたCSVには含まれており、実行時に値を確認しました。',
 'es': 'El informe tiene cinco filas de datos más el encabezado. Los grupos se ordenan por tamaño y hash, y las rutas de cada grupo están ordenadas. La tabla omite la columna SHA-256 para facilitar la lectura; el CSV generado la incluye y sus valores se comprobaron durante la ejecución.',
 'pt-BR': 'O relatório tem cinco linhas de dados e o cabeçalho. Os grupos são ordenados por tamanho e hash, com os caminhos de cada grupo ordenados. A tabela omite a coluna SHA-256 para facilitar a leitura; o CSV gerado a inclui e seus valores foram conferidos na execução.',
}

def main():
 for language in LANGS:
  root = ROOT / ('' if language == 'en' else language)
  for source_path in (ROOT / '_src').glob('*.json'):
   if source_path.name.startswith('_'): continue
   source = json.loads(source_path.read_text(encoding='utf-8'))
   if 'ChatGPT Python tool' not in source.get('verification',{}).get('env',''): continue
   slug = source_path.stem; path = root / 'articles' / slug / 'index.html'
   doc = path.read_text(encoding='utf-8'); strings = COPY[language]
   doc = doc.replace(strings[0], strings[1])
   # All imported verification records are attributed to their execution environment.
   if slug in EDITS:
    ident, index, copy_index = EDITS[slug]
    def edit(soup, section):
     p = section.find_all('p', recursive=False)[index]
     p.clear(); p.append((BOUNDARIES[language] if slug == 'split-large-csv' else '') + strings[copy_index])
     if slug == 'find-duplicate-files':
      first = section.find_all('p', recursive=False)[0]
      first.clear(); first.append(HASH_TABLE[language])
    doc = replace_section(doc, ident, edit)
   def clean(soup, section):
    # These JSON strings had an extra escaping layer in some translations.
    for li in section.find_all('li'):
     if '(?<!' in li.text:
      text = li.text.replace('\\\\', '\\'); li.clear(); li.append(text)
    if slug in RECHECKED:
     ul = section.find('ul', recursive=False)
     if slug == 'ai-email-draft-check' and strings[6] not in ul.text:
      items = ul.find_all('li', recursive=False)
      items[1].clear(); items[1].append(strings[6])
      items[-1].decompose()
     if strings[5] not in ul.text:
      li = soup.new_tag('li'); li.string = strings[5]; ul.append(li)
   doc = replace_section(doc, 'verification', clean)
   path.write_text(doc, encoding='utf-8', newline='')
   if language == 'en':
    rendered = BeautifulSoup(doc, 'html.parser')
    v = rendered.select_one('#verification')
    source['verification']['items'] = [li.text for li in v.find('ul', recursive=False).find_all('li', recursive=False)]
    if slug in EDITS:
     ident, index, _ = EDITS[slug]
     text = rendered.find(id=ident).find_all('p', recursive=False)[index].text
     section = next(s for s in source['sections'] if s['id']==ident)
     [b for b in section['blocks'] if b['type']=='p'][index]['text'] = text
     if slug == 'find-duplicate-files':
      [b for b in section['blocks'] if b['type']=='p'][0]['text'] = HASH_TABLE[language]
    source_path.write_text(json.dumps(source, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
 print('Editorial and provenance corrections applied.')

if __name__ == '__main__': main()
