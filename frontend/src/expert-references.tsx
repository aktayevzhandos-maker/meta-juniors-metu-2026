export function ExpertReferences({text,ids}:{text:string;ids:string[]}){
 if(!ids.length)return <>{text}</>;
 const escaped=[...ids].sort((left,right)=>right.length-left.length).map(id=>id.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));
 const parts=text.split(new RegExp(`(?<![A-Za-z0-9_-])(${escaped.join('|')})(?![A-Za-z0-9_-])`,'g'));
 return <>{parts.map((part,index)=>ids.includes(part)?<a key={index} href={`#${encodeURIComponent(part)}`}>{part}</a>:part)}</>;
}
