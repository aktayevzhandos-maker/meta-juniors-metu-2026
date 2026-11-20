export type DemandRow = {skill:string;requests:number;available_experts:number};
export type SectorRow = {industry:string;available:number;limited:number;busy:number;total:number};
export type BIData = {
 total_requests:number;filtered_requests:number;period_start:string|null;period_end:string;
 skills:DemandRow[];table:DemandRow[];competencies:string[];industries:string[];
 availability_by_industry:SectorRow[];expert_count:number;available_expert_count:number;
 filters:{industry:string|null;skill:string|null};demand_scope:'global';
};
