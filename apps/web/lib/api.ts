import { z } from "zod";
import type { CompareResult, EngineResult, SearchMode } from "./types";

const API = process.env.NEXT_PUBLIC_NEXUS_API_URL ?? "http://localhost:8000/api/v1";

const hitSchema = z.object({
  chunk_id: z.string(), document_id: z.string(), title: z.string(), excerpt: z.string(),
  score: z.number(), department: z.string(), category: z.string(), subcategory: z.string(),
  document_type: z.string(), country: z.string(), version: z.string(), owner_team: z.string(),
  engine: z.enum(["classic", "semantic"]), rank: z.number()
});
const engineSchema = z.object({engine: z.enum(["classic", "semantic"]), latency_ms: z.number(), hits: z.array(hitSchema)});
const compareSchema = z.object({classic: engineSchema, semantic: engineSchema, overlap_document_ids: z.array(z.string()), overlap_ratio: z.number()});

export async function search(mode: SearchMode, query: string): Promise<EngineResult | CompareResult> {
  const endpoint = mode === "compare" ? "compare" : mode;
  const response = await fetch(`${API}/search/${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Nexus-User-Role": "engineer",
      "X-Nexus-User-Department": "Software Engineering",
      "X-Nexus-User-Country": "IN"
    },
    body: JSON.stringify({query, limit: 10, filters: {}}),
    signal: AbortSignal.timeout(8000)
  });
  if (!response.ok) throw new Error(`Search failed (${response.status})`);
  const payload: unknown = await response.json();
  return mode === "compare" ? compareSchema.parse(payload) : engineSchema.parse(payload);
}

export async function getAdminOverview(): Promise<unknown> {
  const response = await fetch(`${API}/admin/overview`, {
    headers: {
      "X-Nexus-User-Role": "admin",
      "X-Nexus-User-Department": "Software Engineering",
      "X-Nexus-User-Country": "IN"
    },
    cache: "no-store"
  });
  if (!response.ok) throw new Error(`Admin API failed (${response.status})`);
  return response.json();
}
