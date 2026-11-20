import {lazy,Suspense,useEffect,useState} from 'react';
import {Navigation,Footer} from './pages';
import {api} from './api';
import {useSectionReveal} from './motion';
import type {BIData} from './bi-types';
const BICharts=lazy(()=>import('./bi-charts'));

export function Analytics(){
 useSectionReveal();
 const [data,setData]=useState<BIData|null>(null);
 const [industry,setIndustry]=useState('');
 const [skill,setSkill]=useState('');
 const [revision,setRevision]=useState(0);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');
 useEffect(()=>{
  const controller=new AbortController();setLoading(true);setError('');
  const params=new URLSearchParams();if(industry)params.set('industry',industry);if(skill)params.set('skill',skill);
  api<BIData>(`analytics/?${params}`,controller.signal).then(setData).catch(e=>{if(!controller.signal.aborted)setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)});
  return()=>controller.abort();
 },[industry,skill,revision]);
 const settled=!!data&&data.filters.industry===(industry||null)&&data.filters.skill===(skill||null);
 return <><header className="topbar"><Navigation/></header><main className="bi-page"><div className="bi-heading"><div><h1>Аналитика экспертизы</h1><p className="intro">Спрос, предложение и доступность специалистов AIID.</p></div><button className="refresh-button" disabled={loading} onClick={()=>setRevision(value=>value+1)}>Обновить</button></div><section className="bi-filters" aria-label="Фильтры аналитики"><div><label htmlFor="bi-industry">Отрасль доступности</label><select id="bi-industry" value={industry} onChange={event=>setIndustry(event.target.value)}><option value="">Все отрасли</option>{data?.industries.map(value=><option key={value}>{value}</option>)}</select></div><div><label htmlFor="bi-skill">Компетенция</label><select id="bi-skill" value={skill} onChange={event=>setSkill(event.target.value)}><option value="">Все компетенции</option>{data?.competencies.map(value=><option key={value}>{value}</option>)}</select></div><button className="refresh-button" disabled={!industry&&!skill} onClick={()=>{setIndustry('');setSkill('')}}>Сбросить выбор</button></section><div className="active-conditions" aria-live="polite"><span>{industry||'Все отрасли'}</span><span>{skill||'Все компетенции'}</span><small>Спрос глобальный · доступность с учётом фильтров</small></div>{loading&&<p role="status" className="bi-loading"><span className="spinner"/> Обновляем аналитику…</p>}{error&&<p role="alert" className="notice error">{error}</p>}{data&&settled&&<div aria-busy={loading}><p className="analytics-period">Период {data.period_start?`${new Date(data.period_start).toLocaleString('ru-RU')} — ${new Date(data.period_end).toLocaleString('ru-RU')}`:'ещё не начат'}. Синтетический реестр.</p><div className="bi-kpis"><section><span>{skill?'Запросов по компетенции':'Всего запросов'}</span><strong>{data.filtered_requests}</strong></section><section><span>Профилей в выборке</span><strong>{data.expert_count}</strong></section><section><span>Доступны сейчас</span><strong>{data.available_expert_count}</strong></section><section><span>Компетенций со спросом</span><strong>{data.table.length}</strong></section></div><Suspense fallback={<p role="status">Загружаем локальные диаграммы…</p>}><BICharts data={data} onSelectSkill={setSkill}/></Suspense><section className="bi-panel bi-table-panel"><h2>Компетенции и доступные эксперты</h2><p>Одна компетенция учитывается один раз за поисковый запрос. Выбор строки фильтрует диаграммы и показатели.</p>{!data.table.length?<p className="chart-empty">Запросов по выбранным условиям пока нет.</p>:<div className="table-scroll"><table><thead><tr><th>Компетенция</th><th>Запросы</th><th>Доступные эксперты, человек</th></tr></thead><tbody>{data.table.map(row=><tr key={row.skill} className={row.requests>0&&row.available_experts===0?'shortage-row':''}><th scope="row"><button aria-pressed={skill===row.skill} onClick={()=>setSkill(row.skill)}>{row.skill}</button>{row.requests>0&&row.available_experts===0&&<span className="shortage-label">Есть спрос, свободных экспертов нет</span>}</th><td>{row.requests}</td><td>{row.available_experts}</td></tr>)}</tbody></table></div>}</section><p className="muted">В PostgreSQL хранятся агрегаты без текстов запросов. Qwen и просмотр страниц не увеличивают счётчики. Фильтр отрасли применяется к реестру, а спрос отражает все отправленные запросы.</p></div>}<Footer/></main></>;
}
