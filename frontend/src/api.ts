export type Expert={id:string;full_name:string;title:string;industry:string;city:string;skills:string[];languages:string[];years_experience:number;availability:'available'|'limited'|'busy';availability_label:string;bio:string;is_synthetic:boolean};
export type Candidate={expert:Expert;score:number;match_percent:number|null;match_status:'full'|'partial';matched_skills:string[];matched_industries:string[];profile_industry:string;missing_requirements:string[];explanation:string[];warnings:string[]};
export type SearchResponse={query:string;status:'ok'|'partial'|'no_matches';results:Candidate[];warnings:string[];elapsed_ms:number;total_experts:number;method:string;semantic_embeddings_used:boolean;parsed_query:{skills:string[];cities:string[];industries:string[];min_years_experience:number|null;max_years_experience?:number|null;excluded_cities?:string[];excluded_industries?:string[];errors?:string[];unrecognized_terms:string[];excluded_skills:string[]}};
export type Health={status:string;expert_count:number;database:string};
export async function api<T>(path:string,signal?:AbortSignal,body?:unknown):Promise<T>{
 const response=await fetch(`/api/v1/${path}`,{signal,method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});
 if(!response.ok){if(response.status===503)throw new Error('Реестр пока недоступен. Проверьте запуск сервисов и загрузку данных.');if(response.status===400){const details=await response.json();throw new Error(Object.values(details).flat().join(' ')||'Проверьте условия запроса.')}throw new Error(`Не удалось получить ответ (HTTP ${response.status}). Попробуйте ещё раз.`)}
 return response.json() as Promise<T>;
}
