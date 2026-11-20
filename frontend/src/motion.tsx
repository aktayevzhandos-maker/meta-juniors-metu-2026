import {useEffect,useRef} from 'react';

export function GlassVisual(){
 const visual=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  const element=visual.current;if(!element)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const mobile=matchMedia('(max-width: 800px)');
  let visible=true;
  let frame=0;
  let entrance:Animation|undefined;
  let disposed=false;
  function staticMode(){return reduced.matches||mobile.matches}
  function update(){frame=0;if(!element)return;element.style.transform=staticMode()?'none':`translateY(${Math.min(scrollY*.1,60)}px)`;element.dataset.motion=staticMode()?'static':'parallax'}
  function scroll(){if(visible&&!frame)frame=requestAnimationFrame(update)}
  function preference(){if(staticMode())entrance?.cancel();update()}
  const image=element.querySelector('img');
  image?.decode().then(()=>{if(disposed||staticMode())return;entrance=image.animate([{opacity:.25,transform:'translateY(28px) rotate(-4deg)'},{opacity:1,transform:'translateY(0) rotate(0)'}],{duration:1050,easing:'cubic-bezier(.16,1,.3,1)'});}).catch(()=>{});
  const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting});observer.observe(element);
  window.addEventListener('scroll',scroll,{passive:true});reduced.addEventListener('change',preference);mobile.addEventListener('change',preference);update();
  return()=>{disposed=true;cancelAnimationFrame(frame);entrance?.cancel();observer.disconnect();window.removeEventListener('scroll',scroll);reduced.removeEventListener('change',preference);mobile.removeEventListener('change',preference)};
 },[]);
 return <div ref={visual} className="hero-visual glass-visual"><img className="glass-image" src="/aiid/hero-glass-cutout.png" alt="Синий стеклянный объект" width="1536" height="1024" fetchPriority="high" decoding="sync"/></div>;
}

export function useSectionReveal(){
 useEffect(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const mobile=matchMedia('(max-width: 800px)');
  const animations=new Set<Animation>();
  function preference(){if(reduced.matches||mobile.matches)animations.forEach(animation=>animation.cancel())}
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
   if(!entry.isIntersecting)return;
   entry.target.setAttribute('data-revealed','true');
   if(!reduced.matches&&!mobile.matches){
    const animation=entry.target.animate([{opacity:.35,transform:'translateY(18px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.16,1,.3,1)'});
    animations.add(animation);animation.finished.then(()=>animations.delete(animation)).catch(()=>animations.delete(animation));
   }
   observer.unobserve(entry.target);
  }),{threshold:.08});
  const seen=new WeakSet<Element>();
  function observe(){document.querySelectorAll('.landing-copy h1,.landing-copy>p,main>section,.search-section,.results,.guide,.landing-guide,.landing-note').forEach(element=>{if(!seen.has(element)){seen.add(element);observer.observe(element)}})}
  observe();const mutations=new MutationObserver(observe);mutations.observe(document.getElementById('root')!,{childList:true,subtree:true});reduced.addEventListener('change',preference);mobile.addEventListener('change',preference);
  return()=>{observer.disconnect();mutations.disconnect();animations.forEach(animation=>animation.cancel());reduced.removeEventListener('change',preference);mobile.removeEventListener('change',preference)};
 },[]);
}
