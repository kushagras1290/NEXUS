export type SearchMode = "classic" | "semantic" | "compare";

export interface SearchHit {
  chunk_id: string;
  document_id: string;
  title: string;
  excerpt: string;
  score: number;
  department: string;
  category: string;
  subcategory: string;
  document_type: string;
  country: string;
  version: string;
  owner_team: string;
  engine: "classic" | "semantic";
  rank: number;
}

export interface EngineResult {
  engine: "classic" | "semantic";
  latency_ms: number;
  hits: SearchHit[];
}

export interface CompareResult {
  classic: EngineResult;
  semantic: EngineResult;
  overlap_document_ids: string[];
  overlap_ratio: number;
}
