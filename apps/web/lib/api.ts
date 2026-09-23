import { z } from "zod";
import type { CompareResult, EngineResult, SearchMode } from "./types";

const API = process.env.NEXT_PUBLIC_NEXUS_API_URL ?? "http://localhost:8000/api/v1";
const DEV_AUTH = process.env.NEXT_PUBLIC_NEXUS_DEV_AUTH === "true";

const hitSchema = z.object({
  chunk_id: z.string(),
  document_id: z.string(),
  title: z.string(),
  excerpt: z.string(),
  score: z.number(),
  department: z.string(),
  category: z.string(),
  subcategory: z.string(),
  document_type: z.string(),
  country: z.string(),
  version: z.string(),
  owner_team: z.string(),
  engine: z.enum(["classic", "semantic"]),
  rank: z.number()
});
const engineSchema = z.object({
  engine: z.enum(["classic", "semantic"]),
  latency_ms: z.number(),
  hits: z.array(hitSchema)
});
const compareSchema = z.object({
  classic: engineSchema,
  semantic: engineSchema,
  overlap_document_ids: z.array(z.string()),
  overlap_ratio: z.number()
});

function devHeaders(role: "engineer" | "admin"): Record<string, string> {
  if (!DEV_AUTH) return {};
  return {
    "X-Nexus-User-Role": role,
    "X-Nexus-User-Department": "Software Engineering",
    "X-Nexus-User-Country": "IN"
  };
}

export async function search(
  mode: SearchMode,
  query: string
): Promise<EngineResult | CompareResult> {
  const endpoint = mode === "compare" ? "compare" : mode;
  const response = await fetch(`${API}/search/${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...devHeaders("engineer")
    },
    body: JSON.stringify({ query, limit: 10, filters: {} }),
    signal: AbortSignal.timeout(8000)
  });
  if (!response.ok) throw new Error(`Search failed (${response.status})`);
  const payload: unknown = await response.json();
  return mode === "compare" ? compareSchema.parse(payload) : engineSchema.parse(payload);
}

export async function getAdminOverview(): Promise<unknown> {
  const response = await fetch(`${API}/admin/overview`, {
    headers: devHeaders("admin"),
    cache: "no-store"
  });
  if (!response.ok) throw new Error(`Admin API failed (${response.status})`);
  return response.json();
}

export async function startReindex(
  limit?: number
): Promise<{ id: string; state: string }> {
  const response = await fetch(`${API}/admin/reindex`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...devHeaders("admin")
    },
    body: JSON.stringify({ limit: limit ?? null, batch_size: 256 })
  });
  if (!response.ok) {
    const detail = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(detail?.detail ?? `Reindex failed (${response.status})`);
  }
  return response.json() as Promise<{ id: string; state: string }>;
}

export async function getReindexStatus(
  jobId: string
): Promise<Record<string, unknown>> {
  const response = await fetch(
    `${API}/admin/reindex/${encodeURIComponent(jobId)}`,
    {
      headers: devHeaders("admin"),
      cache: "no-store"
    }
  );
  if (!response.ok) throw new Error(`Job status failed (${response.status})`);
  return response.json() as Promise<Record<string, unknown>>;
}
