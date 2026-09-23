"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAdminOverview } from "@/lib/api";

type Overview = {
  engines: { classic: {status: string; index: string}; semantic: {status: string; collection: string} };
  dataset: { name: string; source_documents: number; search_chunks: number; evaluation_queries: number };
};

export function AdminConsole() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { getAdminOverview().then((value) => setData(value as Overview)).catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed")); }, []);
  return (
    <main className="admin-shell">
      <aside className="admin-rail"><Link className="brand" href="/">NEXUS<span className="brand-dot">.</span></Link><nav><b>Overview</b><span>Knowledge</span><span>Ingestion</span><span>Search</span><span>Evaluation</span><span>Analytics</span><span>Security</span><span>System</span></nav></aside>
      <section className="admin-main">
        <header><div><div className="eyebrow">CONTROL PLANE</div><h1>Knowledge operations</h1></div><Link href="/search">Open search ↗</Link></header>
        {error && <div className="error-banner">{error}</div>}
        <div className="stat-grid">
          <article><span>Source documents</span><strong>{data?.dataset.source_documents.toLocaleString() ?? "—"}</strong></article>
          <article><span>Search chunks</span><strong>{data?.dataset.search_chunks.toLocaleString() ?? "—"}</strong></article>
          <article><span>Eval queries</span><strong>{data?.dataset.evaluation_queries.toLocaleString() ?? "—"}</strong></article>
          <article><span>Corpus</span><strong>{data?.dataset.name ?? "—"}</strong></article>
        </div>
        <div className="admin-grid">
          <article className="panel"><div className="panel-head"><h2>Retrieval engines</h2><span>LIVE</span></div><div className="engine-row"><div><b>Classic / BM25</b><small>{data?.engines.classic.index ?? "nexus-knowledge-v1"}</small></div><em className={data?.engines.classic.status === "healthy" ? "ok" : "bad"}>{data?.engines.classic.status ?? "loading"}</em></div><div className="engine-row"><div><b>Semantic / HNSW</b><small>{data?.engines.semantic.collection ?? "nexus-knowledge-v1"}</small></div><em className={data?.engines.semantic.status === "healthy" ? "ok" : "bad"}>{data?.engines.semantic.status ?? "loading"}</em></div></article>
          <article className="panel"><div className="panel-head"><h2>Corpus profile</h2><span>11 DOMAINS</span></div><div className="domain-bars">{[["Engineering",82],["SRE",68],["People",64],["Security",51],["Cloud",47],["IT",45]].map(([name,width]) => <div className="bar" key={name}><span>{name}</span><i style={{width: `${width}%`}} /></div>)}</div></article>
        </div>
      </section>
    </main>
  );
}
