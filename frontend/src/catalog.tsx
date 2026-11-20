import {useEffect,useRef,useState} from 'react';
import {api,type Expert} from './api';
import {Navigation,Footer,ImportCsv} from './pages';
import {useSectionReveal} from './motion';

type Registry={count:number;offset:number;limit:number;results:Expert[]};
export function Catalog(){
 useSectionReveal();
 const [industry,setIndustry]=useState('');
 const [industries,setIndustries]=useState<string[]>([]);
 const [offset,setOffset]=useState(0);
 const [revision,setRevision]=useState(0);
 const [data,setData]=useState<Registry|null>(null);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 const [profile,setProfile]=useState<Expert|null>(null);
 const dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const controller=new AbortController();api<{industries:string[]}>('industries/',controller.signal).then(d=>setIndustries(d.industries)).catch(()=>{});return()=>controller.abort()},[]);
 useEffect(()=>{
  const controller=new AbortController();setLoading(true);setError('');
  api<Registry>(`experts/?offset=${offset}&limit=12${industry?`&industry=${encodeURIComponent(industry)}`:''}`,controller.signal)
   .then(setData).catch(e=>{if(!controller.signal.aborted)setError(e.message)})
   .finally(()=>{if(!controller.signal.aborted)setLoading(false)});
  return()=>controller.abort();
 },[industry,offset,revision]);
 useEffect(()=>{
  const id=new URLSearchParams(location.search).get('expert');if(!id)return;
  const controller=new AbortController();
  api<Expert>(`experts/${encodeURIComponent(id)}/`,controller.signal).then(setProfile).catch(e=>{if(!controller.signal.aborted)setError(e.message)});
  return()=>controller.abort();
 },[]);
 useEffect(()=>{if(profile)dialog.current?.showModal()},[profile]);
 return <><header className="topbar"><Navigation/></header><main className="catalog-page"><div className="catalog-heading"><div><h1>Реестр экспертов</h1><p className="intro">Компетенции, опыт и доступность — в одном реестре.</p></div><button className="primary" onClick={()=>{const details=document.querySelector<HTMLDetailsElement>('#registry-import details');if(details){details.open=true;details.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'})}}}>Импорт CSV</button></div><p className="synthetic">Синтетические данные, не содержат реальных персональных данных.</p><div className="catalog-toolbar"><label htmlFor="catalog-industry">Отрасль</label><select id="catalog-industry" value={industry} disabled={loading} onChange={e=>{setIndustry(e.target.value);setOffset(0)}}><option value="">Все отрасли</option>{industries.map(value=><option key={value}>{value}</option>)}</select><strong>{loading?'Обновляем реестр…':data?`${data.count} профилей${industry?' в отрасли':' в реестре'}`:'Загружаем реестр…'}</strong></div>{error&&<p className="notice error" role="alert">{error}</p>}{loading&&<p role="status" className="catalog-loading"><span className="spinner"/> Загружаем профили…</p>}{!loading&&data&&<><div className="catalog-grid">{data.results.map(expert=><article className="catalog-card" key={expert.id}><div className="expert-top"><span>{expert.id}</span><span className={`availability ${expert.availability}`}>{expert.availability_label}</span></div><h2>{expert.full_name}</h2><p>{expert.title}</p><p className="meta">{expert.city} · {expert.years_experience} лет опыта</p><div className="skill-list">{expert.skills.map(skill=><span key={skill}>{skill}</span>)}</div><a className="profile-link" href={`/dashboard/catalog?expert=${encodeURIComponent(expert.id)}`}>Открыть профиль</a></article>)}</div>{!data.results.length&&<p className="empty-result">В этой отрасли профилей пока нет.</p>}<nav className="pagination" aria-label="Страницы каталога"><button className="refresh-button" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-12))}>Назад</button><span>{data.count?`${offset+1}–${Math.min(offset+12,data.count)} из ${data.count}`:'0 профилей'}</span><button className="refresh-button" disabled={offset+12>=data.count} onClick={()=>setOffset(offset+12)}>Далее</button></nav></>}<div id="registry-import"><ImportCsv onApplied={()=>{setOffset(0);setRevision(value=>value+1);api<{industries:string[]}>('industries/').then(data=>setIndustries(data.industries)).catch(()=>{})}}/></div><Footer/></main><dialog ref={dialog} className="catalog-dialog" onClose={()=>{setProfile(null);history.replaceState(null,'','/dashboard/catalog')}} aria-labelledby="catalog-profile-title">{profile&&<><div className="dialog-top"><span>{profile.id} · синтетический профиль</span><button onClick={()=>dialog.current?.close()} aria-label="Закрыть профиль">Закрыть</button></div><h2 id="catalog-profile-title">{profile.full_name}</h2><p>{profile.title}</p><dl><dt>Город</dt><dd>{profile.city}</dd><dt>Отрасль</dt><dd>{profile.industry}</dd><dt>Опыт</dt><dd>{profile.years_experience} лет</dd><dt>Доступность</dt><dd>{profile.availability_label}</dd><dt>Языки</dt><dd>{profile.languages.join(', ')}</dd></dl><div className="skill-list">{profile.skills.map(skill=><span key={skill}>{skill}</span>)}</div><p className="profile-bio">{profile.bio}</p></>}</dialog></>;
}
