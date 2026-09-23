"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { search } from "@/lib/api";
import type { CompareResult, EngineResult, SearchMode } from "@/lib/types";

function isCompare(value: EngineResult | CompareResult): value is CompareResult {
  return "classic" in value && "semantic" in value;
}

function ResultColumn({ result }: { result: EngineResult }) {
  return (
    <section className="result-column">
      <div className="result-meta"><span>{result.engine.toUpperCase()}</span><span>{result.latency_ms.toFixed(1)} ms</span></div>
      {result.hits.map((hit) => (
        <article className="result-card" key={`${hit.engine}-${hit.chunk_id}`}>
          <div className="rank">{String(hit.rank).padStart(2, "0")}</div>
          <div><h3>{hit.title}</h3><p>{hit.excerpt}</p><div className="chips"><span>{hit.department}</span><span>{hit.document_type}</span><span>{hit.country}</span><span>v{hit.version}</span></div></div>
        </article>
      ))}
      {!result.hits.length && <div className="empty-state">No accessible results.</div>}
    </section>
  );
}

export function SearchWorkspace() {
  const [mode, setMode] = useState<SearchMode>("compare");
  const [query, setQuery] = useState("The standard deployment pipeline is broken. How do I ship an urgent production fix?");
  const [result, setResult] = useState<EngineResult | CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError(null);
    try { setResult(await search(mode, query)); }
    catch (err) { setError(err instanceof Error ? err.message : "Search failed"); }
    finally { setLoading(false); }
  }

  return (
    <main className="workspace">
      <div className="workspace-noise" aria-hidden="true" />
      <nav className="workspace-nav"><Link className="brand" href="/">NEXUS<span className="brand-dot">.</span></Link><Link href="/admin">ADMIN ↗</Link></nav>
      <section className="query-stage">
        <div className="eyebrow">SEARCH THE ORGANISATION</div>
        <form onSubmit={submit}>
          <textarea aria-label="Search query" value={query} onChange={(e) => setQuery(e.target.value)} maxLength={1000} />
          <div className="query-controls">
            <div className="mode-switch" aria-label="Search mode">
              {(["classic", "semantic", "compare"] as const).map((item) => <button type="button" key={item} className={mode === item ? "active" : ""} onClick={() => setMode(item)}>{item}</button>)}
            </div>
            <button className="search-button" disabled={loading || query.trim().length < 2}>{loading ? "SEARCHING" : "SEARCH"}<span>↗</span></button>
          </div>
        </form>
      </section>
      {error && <div className="error-banner">{error}</div>}
      {result && (
        <section className="results-stage">
          {isCompare(result) ? <><div className="comparison-bar"><span>RESULT OVERLAP</span><strong>{Math.round(result.overlap_ratio * 100)}%</strong></div><div className="compare-grid"><ResultColumn result={result.classic}/><ResultColumn result={result.semantic}/></div></> : <ResultColumn result={result}/>} 
        </section>
      )}
    </main>
  );
}
