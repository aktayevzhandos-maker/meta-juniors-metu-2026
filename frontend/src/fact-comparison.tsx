import type {Candidate,SearchResponse} from './api';

type Cell={value:string;note:string;tone:'good'|'caution'|'neutral'};
export function FactComparison({candidates,parsed}:{candidates:Candidate[];parsed:SearchResponse['parsed_query']}){
 if(candidates.length<2)return <p className="muted">Отметьте двух или трёх кандидатов в результатах, чтобы сравнить их рядом.</p>;
 const rows:{label:string;cells:Cell[]}[]=[];
 for(const skill of parsed.skills){
  rows.push({label:`Навык · ${skill}`,cells:candidates.map(candidate=>{
   const matched=candidate.matched_skills.includes(skill);
   return {value:skill,note:matched?'Условие выполнено':'В профиле не указан',tone:matched?'good':'caution'};
  })});
 }
 rows.push({label:'Город',cells:candidates.map(candidate=>{
  const city=candidate.expert.city;
  const specified=parsed.cities.length>0||(parsed.excluded_cities?.length||0)>0;
  const matched=(!parsed.cities.length||parsed.cities.includes(city))&&!parsed.excluded_cities?.includes(city);
  return {value:city,note:specified?(matched?'Условие города выполнено':'Не соответствует городу'):'Город не задан',tone:specified?(matched?'good':'caution'):'neutral'};
 })});
 rows.push({label:'Стаж',cells:candidates.map(candidate=>{
  const years=candidate.expert.years_experience;
  const minimum=parsed.min_years_experience,maximum=parsed.max_years_experience;
  const specified=minimum!==null||maximum!=null;
  const matched=(minimum===null||years>=minimum)&&(maximum==null||years<=maximum);
  let note='Стаж не ограничен';
  if(specified)note=matched?'Условие стажа выполнено':maximum!=null&&years>maximum?`Превышает максимум ${maximum} лет`:`Ниже минимума ${minimum} лет`;
  return {value:new Intl.NumberFormat('ru',{style:'unit',unit:'year',unitDisplay:'long'}).format(years),note,tone:specified?(matched?'good':'caution'):'neutral'};
 })});
 rows.push({label:'Доступность',cells:candidates.map(candidate=>({value:candidate.expert.availability_label,note:candidate.expert.availability==='available'?'Доступен сейчас':candidate.expert.availability==='limited'?'Доступность ограничена':'Сейчас занят',tone:candidate.expert.availability==='available'?'good':'caution'}))});
 return <div className="table-scroll fact-comparison" tabIndex={0} role="region" aria-label="Сравнение по условиям запроса"><table><thead><tr><th>Условие запроса</th>{candidates.map(candidate=><th key={candidate.expert.id}><a href={`#${candidate.expert.id}`}>{candidate.expert.id}</a><span>{candidate.expert.full_name}</span></th>)}</tr></thead><tbody>{rows.map(row=><tr key={row.label}><th scope="row">{row.label}</th>{row.cells.map((cell,index)=><td key={candidates[index].expert.id}><div className={`fact-cell ${cell.tone}`}><strong>{cell.value}</strong><span>{cell.note}</span></div></td>)}</tr>)}</tbody></table><p className="muted comparison-legend">Зелёный — условие выполнено или эксперт доступен. Янтарный — условие не выполнено или доступность ограничена. Равные условия отмечены одинаково.</p></div>;
}
