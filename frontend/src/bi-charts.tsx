import {useEffect,useRef} from 'react';
import * as echarts from 'echarts/core';
import {BarChart} from 'echarts/charts';
import {GridComponent,TooltipComponent,LegendComponent,AriaComponent} from 'echarts/components';
import {SVGRenderer} from 'echarts/renderers';
import type {BIData} from './bi-types';

echarts.use([BarChart,GridComponent,TooltipComponent,LegendComponent,AriaComponent,SVGRenderer]);

export default function BICharts({data,onSelectSkill}:{data:BIData;onSelectSkill:(skill:string)=>void}){
 const demand=useRef<HTMLDivElement>(null);
 const availability=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!demand.current||!availability.current)return;
  const demandChart=echarts.init(demand.current,null,{renderer:'svg'});
  const supplyChart=echarts.init(availability.current,null,{renderer:'svg'});
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const rows=[...data.skills].reverse();
  demandChart.setOption({
   animation:!reduced.matches,animationDuration:350,aria:{enabled:true},
   tooltip:{trigger:'axis',renderMode:'richText',axisPointer:{type:'shadow'}},
   grid:{left:12,right:42,top:20,bottom:36,containLabel:true},
   xAxis:{type:'value',minInterval:1,name:'Запросов',nameLocation:'middle',nameGap:24,splitLine:{lineStyle:{color:'#e7eef8'}}},
   yAxis:{type:'category',data:rows.map(row=>row.skill),axisLabel:{width:140,overflow:'truncate',color:'#0e2347'},axisLine:{show:false},axisTick:{show:false}},
   series:[{name:'Запросов',type:'bar',data:rows.map(row=>({value:row.requests,name:row.skill})),barMaxWidth:24,itemStyle:{color:'#154bcd',borderRadius:[0,5,5,0]},label:{show:true,position:'right',color:'#0e2347'}}],
  });
  demandChart.on('click',params=>{if(params.componentType==='series')onSelectSkill(params.name)});
  supplyChart.setOption({
   animation:!reduced.matches,animationDuration:350,aria:{enabled:true},
   tooltip:{trigger:'axis',renderMode:'richText',axisPointer:{type:'shadow'}},
   legend:{bottom:0,textStyle:{color:'#465d80',fontSize:12}},
   grid:{left:10,right:12,top:26,bottom:90,containLabel:true},
   xAxis:{type:'category',data:data.availability_by_industry.map(row=>row.industry),axisLabel:{interval:0,rotate:25,fontSize:12,width:90,overflow:'truncate'}},
   yAxis:{type:'value',minInterval:1,name:'Человек',splitLine:{lineStyle:{color:'#e7eef8'}}},
   series:[
    {name:'Доступны',type:'bar',stack:'availability',data:data.availability_by_industry.map(row=>row.available),itemStyle:{color:'#29875d'},barMaxWidth:36},
    {name:'Ограниченно',type:'bar',stack:'availability',data:data.availability_by_industry.map(row=>row.limited),itemStyle:{color:'#d9a23d'}},
    {name:'Заняты',type:'bar',stack:'availability',data:data.availability_by_industry.map(row=>row.busy),itemStyle:{color:'#9baec9'}},
   ],
  });
  const resize=new ResizeObserver(()=>{demandChart.resize();supplyChart.resize()});
  resize.observe(demand.current);resize.observe(availability.current);
  function preference(){demandChart.setOption({animation:!reduced.matches});supplyChart.setOption({animation:!reduced.matches})}
  reduced.addEventListener('change',preference);
  return()=>{resize.disconnect();reduced.removeEventListener('change',preference);demandChart.dispose();supplyChart.dispose()};
 },[data,onSelectSkill]);
 return <div className="bi-charts"><section className="bi-panel"><h2>Топ-5 по спросу</h2><p>Запросы по всему реестру. Нажмите на бар, чтобы выбрать компетенцию.</p>{!data.skills.length&&<p className="chart-empty">Поисковых запросов с распознанными компетенциями пока нет.</p>}<div className="echart" ref={demand} role="img" aria-label="Горизонтальная диаграмма спроса, запросов. Значения также приведены в таблице."/></section><section className="bi-panel"><h2>Доступность по отраслям</h2><p>Профили в текущей выборке, человек.</p>{!data.availability_by_industry.length&&<p className="chart-empty">В выбранной отрасли нет экспертов с этой компетенцией.</p>}<div className="echart" ref={availability} role="img" aria-label="Доступные, ограниченно доступные и занятые эксперты по отраслям."/></section></div>;
}
