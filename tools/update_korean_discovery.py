"""Maintain descriptive Korean landing-page copy for existing tutorial content."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
COPY={
 '':('AI 활용법·파이썬 업무 자동화 무료 튜토리얼 | 워크노트','AI 활용법부터 파이썬 업무 자동화, 엑셀 데이터 정리까지 예제로 배우는 무료 튜토리얼입니다. 프롬프트 작성, CSV 병합, 문서 요약과 결과 검증을 단계별로 따라 해 보세요.','AI 활용과 업무 자동화, 예제로 시작하세요'),
 'about/':('AI 활용·엑셀·파이썬 실습 사이트 소개 | 워크노트','코딩 입문자와 일반인을 위한 AI 활용법, 파이썬 업무 자동화, 엑셀 데이터 정리 튜토리얼을 제공합니다. 예제와 확인 기준으로 직접 배우는 워크노트를 소개합니다.','워크노트: AI 활용과 업무 자동화를 배우는 곳'),
 'category/ai/':('AI 활용법과 프롬프트 작성·답변 검증 | 워크노트','AI 초보자를 위한 프롬프트 작성법, AI 공부법, 주간 계획 만들기부터 업무 이메일·문서 요약·엑셀 수식 검증까지 다룹니다. 요청문 예시와 확인 기준을 따라 실습하세요.','AI 활용법·프롬프트 작성과 결과 검증'),
 'category/automation/':('파이썬 업무 자동화: 파일 정리·CSV 합치기 | 워크노트','파이썬으로 파일 이름 일괄 변경, 중복 파일 찾기, CSV 파일 합치기와 분할을 실습합니다. 원본을 보존하며 반복 작업을 자동화하는 예제와 실행 방법을 확인하세요.','파이썬 파일 정리·반복 업무 자동화'),
 'category/office/':('엑셀 데이터 정리·문서 자동화 예제 | 워크노트','엑셀 중복 데이터 찾기, 여러 시트 합치기, 날짜 형식 통일과 월별 집계를 예제로 배웁니다. 표와 문서를 정리하는 업무 자동화 방법을 단계별로 확인하세요.','엑셀 데이터 정리와 문서 업무 자동화'),
 'category/automotive/':('파이썬 데이터 분석: 이동평균·FFT·단위 변환 | 워크노트','자동차 시험을 본뜬 합성 데이터로 파이썬 데이터 분석을 연습합니다. 이동평균, FFT 주파수 분석, 시험 결과 비교와 단위 변환을 예제 수치로 확인하세요.','자동차 시험 예제로 배우는 데이터 분석'),
 'category/research/':('자료 조사·참고문헌 관리·설문 데이터 정리 | 워크노트','자료 조사에서 출처와 기준일을 기록하고 참고문헌 목록, 데이터 사전, 설문 데이터를 정리하는 방법을 배웁니다. 연구와 보고서 작성에 활용할 예제와 점검 기준을 제공합니다.','자료 조사와 연구 데이터 정리'),
 'category/collaboration/':('회의록 할 일 정리·업무 인수인계 체크리스트 | 워크노트','회의록에서 실행할 일을 정리하고 업무 인수인계 체크리스트, 파일명 규칙과 변경 로그를 만드는 방법을 배웁니다. 팀 협업에 활용할 양식과 예제를 확인하세요.','회의 후속 업무와 인수인계 정리'),
}
def main():
 for route,(title,description,heading) in COPY.items():
  p=ROOT/'ko'/route/'index.html'; s=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
  s.title.string=title; s.h1.string=heading
  for selector,value in [('meta[name="description"]',description),('meta[property="og:description"]',description),('meta[property="og:title"]',title)]: s.select_one(selector)['content']=value
  s.select_one('.page-intro').string=description
  for script in s.select('script[type="application/ld+json"]'):
   data=json.loads(script.string)
   if data.get('@type') in ('CollectionPage','WebPage'):
    data['name']=heading; data['description']=description; script.string=json.dumps(data,ensure_ascii=False)
  if route=='about/':
   sections=s.select('.reading-content > section'); paragraphs=sections[0].find_all('p')
   paragraphs[0].string='코딩 입문자, 사무직, 학생, 연구원은 물론 일상에서 AI를 더 잘 활용하고 싶은 일반인을 위한 무료 튜토리얼입니다. AI에게 질문하는 방법과 답변 확인부터 파이썬으로 반복 업무 줄이기, 엑셀·CSV 데이터 정리, 자료 조사와 팀 협업까지 작은 예제로 배웁니다.'
   paragraphs[1].string='각 글은 필요한 준비와 따라 할 순서, 예제, 결과를 확인할 기준과 한계를 설명합니다. 코드 실습 글에서는 제공된 예제 파일을 활용하고, AI 입문 글에서는 본문의 요청문을 복사해 연습할 수 있습니다.'
   existing=s.find(id='learning-paths')
   if existing: existing.decompose()
   section=s.new_tag('section',id='learning-paths'); h=s.new_tag('h2'); h.string='배우고 싶은 작업부터 시작하세요'; section.append(h); ul=s.new_tag('ul')
   links=[('ai-clear-request','AI 프롬프트 작성법: 목적·상황·조건을 담아 질문하기'),('ai-practice-tutor','AI 공부법: 정답 대신 힌트와 오답 복습 활용하기'),('ai-weekly-plan','AI 일정 관리: 가능한 시간으로 주간 계획 만들기'),('merge-csv','파이썬 CSV 파일 합치기: 원본 파일명을 남겨 데이터 병합하기'),('excel-duplicates','엑셀 중복 데이터 찾기: 표를 정리하기 전에 확인하기'),('ai-summary-source-check','AI 문서 요약 검증: 원문과 요약을 대조하기')]
   for slug,label in links:
    li=s.new_tag('li'); a=s.new_tag('a',href='/ko/articles/'+slug+'/'); a.string=label; li.append(a); ul.append(li)
   section.append(ul); sections[0].insert_after(section)
   sections[1].find_all('p')[1].string='광고 계정 연결은 아직 준비 중이며 현재 광고를 게재하지 않습니다. 방문 통계에는 Google Analytics를 사용합니다. 사이트에서 외부 AI API를 호출하는 기능은 없습니다.'
  p.write_text(str(s),encoding='utf-8',newline='')
 ns='http://www.sitemaps.org/schemas/sitemap/0.9'; ET.register_namespace('',ns); p=ROOT/'sitemap.xml'; tree=ET.parse(p)
 urls={'https://worknotetips.com/ko/'+r for r in COPY}
 for e in tree.getroot():
  if e.find('{'+ns+'}loc').text in urls:
   last=e.find('{'+ns+'}lastmod')
   if last is None: last=ET.SubElement(e,'{'+ns+'}lastmod')
   last.text='2026-09-22'
 tree.write(p,encoding='utf-8',xml_declaration=True)
 print('Updated 8 Korean landing pages and sitemap.')
if __name__=='__main__': main()
