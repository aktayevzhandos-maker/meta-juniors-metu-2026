"""New team-authored stress set. Oracle reads CSV, never imports retrieval code.

This is not an independent human blind benchmark: its author has seen the code.
Definitions/expected IDs are saved before the first HTTP search. No DB mutations.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'testing'

def case(name, query, skills=(), city=None, **rules):
    return dict(id=name, query=query, skills=list(skills), city=city, **rules)

CASES = [
    case('quality-lean', 'Бережливое производство и ISO 9001, Алматы', ['Lean','ISO 9001'], 'Алматы'),
    case('clinical-gcp', 'Клинические испытания по GCP в Караганде', ['Клинические исследования','GCP'], 'Караганда'),
    case('drug-registration', 'Регистрация препаратов и фармаконадзор, Шымкент', ['Регистрация лекарств','Фармаконадзор'], 'Шымкент'),
    case('industrial-security', 'SCADA и защита АСУ ТП в Шымкенте', ['SCADA','Безопасность АСУ ТП'], 'Шымкент'),
    case('vision', 'Python и распознавание дефектов, Атырау', ['Python','Компьютерное зрение'], 'Атырау'),
    case('deployment', 'K8s и внедрение моделей в Алматы', ['Kubernetes','MLOps'], 'Алматы'),
    case('stem', 'Инженерное образование и робототехника, Алматы', ['STEM','Робототехника'], 'Алматы'),
    case('food-safety', 'HACCP и производственный аудит в Астане', ['HACCP','Аудит производства'], 'Астана'),
    case('certification', 'ISO 27001 и EAC, Атырау', ['ISO 27001','Сертификация ЕАЭС'], 'Атырау'),
    case('senior-nlp', 'NLP и Python, минимум 18 лет', ['NLP','Python'], min_years=18),
    case('senior-pharma', 'GMP в фармацевтике от 18 лет', ['GMP'], industry='Фармацевтика', min_years=18),
    case('alternative', 'Нужен SCADA или PLC', ['SCADA','PLC'], any_skill=True),
    case('strict-city', 'Только Алматы, нужен ISO 9001', ['ISO 9001'], 'Алматы'),
    case('excluded-city', 'GMP, но не из Алматы', ['GMP'], excluded_city='Алматы'),
    case('max-experience', 'GMP, опыт не более 10 лет', ['GMP'], max_years=10),
    case('exclusion-tail', 'SCADA без PLC', ['SCADA'], excluded_skills=['PLC']),
    case('exclusion-front', 'Без PLC нужен специалист по SCADA', ['SCADA'], excluded_skills=['PLC']),
    case('industry-exclusion', 'Фармацевтика от 5 лет без Python', industry='Фармацевтика', min_years=5, excluded_skills=['Python']),
    case('learning', 'СДО и дизайн обучения в Атырау', ['LMS','Instructional Design'], 'Атырау'),
    case('frontend', 'Нужен разработчик интерфейсов на React', ['React']),
    case('unknown-city', 'GMP в Ташкенте', ['GMP'], 'Ташкент', negative=True),
    case('unknown-specialty', 'Нужен специалист по квантовой криптографии в Астане', ['Квантовая криптография'], 'Астана', negative=True),
    case('impossible-skills', 'Обязательно одновременно GMP, SCADA и BIM', ['GMP','SCADA','BIM'], negative=True),
    case('impossible-experience', 'Нужен Python с опытом от 50 лет', ['Python'], min_years=50, negative=True),
    case('impossible-combination', 'GCP и пентест, обе компетенции обязательны', ['GCP','Пентест'], negative=True),
]

def relevant(expert, spec):
    skills = set(expert['skills'].split('|'))
    wanted = set(spec['skills'])
    if wanted and not (bool(skills & wanted) if spec.get('any_skill') else wanted <= skills): return False
    if spec.get('city') and expert['city'] != spec['city']: return False
    if spec.get('excluded_city') == expert['city']: return False
    if spec.get('industry') and expert['industry'] != spec['industry']: return False
    if skills & set(spec.get('excluded_skills', [])): return False
    years = int(expert['years_experience'])
    return years >= spec.get('min_years', 0) and years <= spec.get('max_years', 60)

def request(path, body=None, base='http://127.0.0.1:8000/api/v1/'):
    req = urllib.request.Request(base + path, data=json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None,
                                 headers={'Content-Type':'application/json'})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            return response.status, json.load(response), (time.perf_counter()-started)*1000
    except urllib.error.HTTPError as error:
        return error.code, json.load(error), (time.perf_counter()-started)*1000

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = (ROOT/'data/experts.csv').read_bytes()
    with (ROOT/'data/experts.csv').open(encoding='utf-8-sig',newline='') as stream: experts = list(csv.DictReader(stream))
    by_id = {expert['id']:expert for expert in experts}
    definitions = []
    for spec in CASES:
        expected = [expert['id'] for expert in experts if relevant(expert,spec)]
        assert bool(expected) != bool(spec.get('negative')), (spec['id'], 'Incorrect oracle assumptions')
        definitions.append(dict(spec,relevant_ids=expected))
    manifest = {'dataset_sha256':hashlib.sha256(raw).hexdigest(), 'cases':definitions,
                'provenance':'Team-authored stress set; author saw implementation. Expectations frozen before HTTP calls, no tuning during run.'}
    frozen = json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    (OUT/'acceptance_cases.json').write_text(frozen,encoding='utf-8')
    manifest_hash = hashlib.sha256(frozen.encode()).hexdigest()
    rows, evidence_errors, times = [], [], []
    for spec in definitions:
        status, payload, elapsed = request('search/', {'query':spec['query'],'limit':3})
        times.append(elapsed)
        candidates = payload.get('results',[])
        ids = [item['expert']['id'] for item in candidates]
        hit = bool(set(ids)&set(spec['relevant_ids']))
        false_full = [item['expert']['id'] for item in candidates if item['match_status']=='full' and item['expert']['id'] not in spec['relevant_ids']]
        for item in candidates:
            saved = by_id.get(item['expert']['id'])
            if not saved or not set(item['matched_skills']) <= set(saved['skills'].split('|')) or item['profile_industry']!=saved['industry']:
                evidence_errors.append({'case':spec['id'],'expert':item['expert']['id']})
        passed = status==200 and (not false_full if spec.get('negative') else hit)
        rows.append({'id':spec['id'],'query':spec['query'],'negative':bool(spec.get('negative')),'http_status':status,
                     'hit_at_3':hit if not spec.get('negative') else None,'passed':passed,'top3':ids,
                     'false_full_against_oracle':false_full,'elapsed_ms':round(elapsed,3),'response':payload})
    checks=[]
    for body in [{}, {'query':'12'}, {'query':'GMP','limit':2}, {'query':'GMP','industry':'unknown'}]:
        status,_,_=request('search/',body); checks.append({'kind':'invalid_input','body':body,'status':status,'passed':status==400})
    status,payload,_=request('search/',{'query':'Python','industry':'IT'})
    checks.append({'kind':'industry_filter','passed':status==200 and bool(payload['results']) and all(x['expert']['industry']=='IT' for x in payload['results'])})
    # Inspect availability monotonicity only for identical skills/city/industry/experience.
    status, availability, _=request('search/',{'query':'GMP','limit':20})
    pairs=[]
    for a in availability.get('results',[]):
        for b in availability.get('results',[]):
            ae,be=a['expert'],b['expert']
            if ae['availability']=='available' and be['availability']=='busy' and all(ae[k]==be[k] for k in ['skills','city','industry','years_experience']):
                pairs.append(a['score']>b['score'])
    # Most synthetic records differ in years/city: don't claim a paired check from no comparable pair.
    checks.append({'kind':'availability_identical_profiles','comparable_pairs':len(pairs),'passed':all(pairs) if pairs else None})
    proxy_status,proxy,_=request('search/',{'query':'GMP и клинические исследования в Алматы'},base='http://127.0.0.1:5173/api/v1/')
    checks.append({'kind':'frontend_proxy','passed':proxy_status==200 and 'EXP-001' in [r['expert']['id'] for r in proxy['results']]})
    positives=[r for r in rows if not r['negative']]
    report={'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'working_tree_contains_uncommitted_frontend':bool(subprocess.check_output(['git','status','--porcelain','--','frontend'],cwd=ROOT,text=True).strip()),
        'search_source_sha256':hashlib.sha256((ROOT/'backend/experts/search/engine.py').read_bytes()).hexdigest(),
        'manifest_sha256':manifest_hash,'dataset_sha256':manifest['dataset_sha256'],
        'scope':'Real localhost HTTP API, read-only production registry; no physical internet disconnection, no Qwen',
        'positive_count':len(positives),'hits':sum(r['hit_at_3'] for r in positives),'hit_at_3':sum(r['hit_at_3'] for r in positives)/len(positives),
        'negative_count':5,'negative_passed':sum(r['passed'] for r in rows if r['negative']),
        'acceptance_passed':all(r['passed'] and not r['false_full_against_oracle'] for r in rows),
        'false_full_count':sum(len(r['false_full_against_oracle']) for r in rows),
        'evidence_errors':evidence_errors,'latency_ms':{'median':round(statistics.median(times),3),'p95':round(sorted(times)[math.ceil(.95*len(times))-1],3),'max':round(max(times),3)},
        'checks':checks,'cases':rows,'independent_blind_benchmark':False}
    (OUT/'acceptance_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False,indent=2))
    print('FAILED CASES:')
    for row in rows:
        if not row['passed'] or row['false_full_against_oracle']:
            print(row['id'], row['query'], 'hit=',row['hit_at_3'],'false_full=',row['false_full_against_oracle'],'top3=',row['top3'])
    if not report['acceptance_passed']:
        raise SystemExit(1)

if __name__=='__main__': main()
