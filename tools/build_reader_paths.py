"""Add a small, outcome-led entry point using existing verified articles."""
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ['ai-clear-request', 'ai-presentation-outline', 'ai-compare-document-versions', 'team-ai-where-to-start']
COPY = {
 'en': ['What would you like to make today?', 'Pick one small task. Use the sample, copy the prompt, then check the result.', 'A clearer AI request', 'A presentation outline', 'A document change list', 'Your team’s first AI task', 'Start with a sample →', 'Analytics on this browser', 'We measure tutorial opens and successful copy actions, without sending the copied text or search terms in these events. You can turn analytics off on this browser. This preference is stored locally; it also lets site editors exclude their own checks. Clearing browser storage resets it.', 'Turn analytics off', 'Turn analytics on', 'Off', 'On'],
 'ko': ['오늘 AI로 무엇을 만들어 볼까요?', '작은 과제 하나를 고르세요. 예제를 읽고 → 요청문을 복사하고 → 결과를 확인합니다.', '원하는 답을 얻는 AI 요청문', '발표에 쓸 슬라이드 개요', '문서의 변경사항 비교표', '우리 팀의 첫 AI 적용 업무', '예제로 시작하기 →', '이 브라우저의 방문 통계', '글 열기와 복사 성공을 측정하며, 이 이벤트에 복사한 내용이나 검색어는 보내지 않습니다. 이 브라우저에서 통계를 끌 수 있습니다. 선택은 브라우저에 저장되며 운영자의 검수 방문을 제외할 때도 사용할 수 있습니다. 브라우저 저장 공간을 지우면 선택이 초기화됩니다.', '방문 통계 끄기', '방문 통계 켜기', '꺼짐', '켜짐'],
 'ja': ['今日はAIで何を作りますか？', '小さな課題を一つ選びましょう。例を読み、プロンプトをコピーして、結果を確認します。', '意図が伝わるAIへの依頼文', 'プレゼンの構成案', '文書の変更点一覧', 'チームで最初にAIを使う業務', '例から始める →', 'このブラウザのアクセス解析', '記事を開いた操作とコピー成功を測定します。これらのイベントにコピー内容や検索語は送信しません。このブラウザの解析をオフにできます。設定はブラウザ内に保存され、運営者の確認作業の除外にも使えます。ブラウザの保存データを削除すると設定はリセットされます。', '解析をオフにする', '解析をオンにする', 'オフ', 'オン'],
 'es': ['¿Qué quieres crear hoy con IA?', 'Elige una tarea pequeña. Lee el ejemplo, copia la instrucción y comprueba el resultado.', 'Una petición clara para la IA', 'Un esquema de presentación', 'Una lista de cambios del documento', 'La primera tarea con IA de tu equipo', 'Empezar con un ejemplo →', 'Analítica en este navegador', 'Medimos la apertura de tutoriales y las copias realizadas, sin enviar el texto copiado ni las búsquedas en estos eventos. Puedes desactivar la analítica en este navegador. La preferencia se guarda localmente y también permite excluir las revisiones del equipo editorial. Borrar los datos del navegador restablece la preferencia.', 'Desactivar analítica', 'Activar analítica', 'Desactivada', 'Activada'],
 'pt-BR': ['O que você quer criar com IA hoje?', 'Escolha uma tarefa pequena. Leia o exemplo, copie o pedido e confira o resultado.', 'Um pedido claro para a IA', 'Um roteiro de apresentação', 'Uma lista de alterações no documento', 'A primeira tarefa com IA da sua equipe', 'Começar com um exemplo →', 'Estatísticas neste navegador', 'Medimos a abertura de tutoriais e as cópias concluídas, sem enviar o texto copiado ou os termos de busca nesses eventos. Você pode desativar as estatísticas neste navegador. A preferência fica salva localmente e também permite excluir as verificações da equipe editorial. Limpar os dados do navegador redefine a preferência.', 'Desativar estatísticas', 'Ativar estatísticas', 'Desativadas', 'Ativadas'],
}

def build():
 for lang, c in COPY.items():
  prefix = '' if lang == 'en' else lang + '/'
  p = ROOT / prefix / 'index.html'
  s = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
  if old := s.select_one('#start-here'): old.decompose()
  section = s.new_tag('section', id='start-here', attrs={'class':'starter-paths', 'aria-labelledby':'start-title'})
  h = s.new_tag('h2', id='start-title'); h.string=c[0]; section.append(h)
  intro=s.new_tag('p'); intro.string=c[1]; section.append(intro)
  grid=s.new_tag('div', attrs={'class':'starter-grid'})
  for i, slug in enumerate(SLUGS):
   article=ROOT / prefix / 'articles' / slug / 'index.html'
   assert article.exists(), article
   a=s.new_tag('a', href=f'/{prefix}articles/{slug}/', attrs={'class':'starter-card','data-starter':slug})
   strong=s.new_tag('strong'); strong.string=c[2+i]; a.append(strong)
   small=s.new_tag('span'); small.string=c[6]; a.append(small); grid.append(a)
  section.append(grid)
  s.select_one('#search').insert_before(section)
  p.write_text(str(s), encoding='utf-8')
  p=ROOT / prefix / 'privacy/index.html'
  s=BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
  if old:=s.select_one('#analytics-choice'): old.decompose()
  section=s.new_tag('section',id='analytics-choice')
  h=s.new_tag('h2'); h.string=c[7]; section.append(h)
  para=s.new_tag('p'); para.string=c[8]; section.append(para)
  for value, label in [('off',c[9]),('on',c[10])]:
   b=s.new_tag('button',type='button',attrs={'data-analytics-choice':value}); b.string=label; section.append(b)
  status=s.new_tag('p',attrs={'data-analytics-status':'','data-off':c[11],'data-on':c[12],'role':'status'});section.append(status)
  s.select_one('.reading-content').append(section)
  p.write_text(str(s),encoding='utf-8')
 print('Updated 5 home pages and 5 privacy pages.')

if __name__ == '__main__': build()
