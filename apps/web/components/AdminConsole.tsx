"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  getAdminOverview,
  getReindexStatus,
  startReindex
} from "@/lib/api";

type Job = {
  id: string;
  state: string;
  indexed_chunks?: number | null;
  documents_loaded?: number | null;
  error?: string | null;
};

type Overview = {
  engines: {
    classic: { status: string; index: string };
    semantic: { status: string; collection: string };
  };
  dataset: {
    name: string;
    source_documents: number;
    search_chunks: number;
    evaluation_queries: number;
    path: string;
  };
  latest_reindex_job: Job | null;
};

export function AdminConsole() {
  const [data, setData] = useState<Overview | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const refresh = useCallback(async () => {
    const value = (await getAdminOverview()) as Overview;
    setData(value);
    setJob(value.latest_reindex_job);
  }, []);

  useEffect(() => {
    refresh().catch((cause: unknown) =>
      setError(cause instanceof Error ? cause.message : "Failed")
    );
  }, [refresh]);

  useEffect(() => {
    if (!job?.id || !["queued", "running"].includes(job.state)) return;

    const timer = window.setInterval(() => {
      getReindexStatus(job.id)
        .then((value) => setJob(value as Job))
        .catch((cause: unknown) =>
          setError(cause instanceof Error ? cause.message : "Job status failed")
        );
    }, 2000);

    return () => window.clearInterval(timer);
  }, [job?.id, job?.state]);

  async function reindex() {
    setStarting(true);
    setError(null);
    try {
      setJob(await startReindex());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Reindex failed");
    } finally {
      setStarting(false);
    }
  }

  const jobBusy =
    starting || job?.state === "queued" || job?.state === "running";

  return (
    <main className="admin-shell">
      <aside className="admin-rail">
        <Link className="brand" href="/">
          NEXUS<span className="brand-dot">.</span>
        </Link>
        <nav>
          <b>Overview</b>
          <span>Knowledge</span>
          <span>Ingestion</span>
          <span>Search</span>
          <span>Evaluation</span>
          <span>Analytics</span>
          <span>Security</span>
          <span>System</span>
        </nav>
      </aside>

      <section className="admin-main">
        <header>
          <div>
            <div className="eyebrow">CONTROL PLANE</div>
            <h1>Knowledge operations</h1>
          </div>
          <Link href="/search">Open search ↗</Link>
        </header>

        {error && <div className="error-banner">{error}</div>}

        <div className="stat-grid">
          <article>
            <span>Source documents</span>
            <strong>{data?.dataset.source_documents.toLocaleString() ?? "—"}</strong>
          </article>
          <article>
            <span>Search chunks</span>
            <strong>{data?.dataset.search_chunks.toLocaleString() ?? "—"}</strong>
          </article>
          <article>
            <span>Eval queries</span>
            <strong>{data?.dataset.evaluation_queries.toLocaleString() ?? "—"}</strong>
          </article>
          <article>
            <span>Corpus</span>
            <strong>{data?.dataset.name ?? "—"}</strong>
          </article>
        </div>

        <div className="admin-grid">
          <article className="panel">
            <div className="panel-head">
              <h2>Retrieval engines</h2>
              <span>LIVE</span>
            </div>
            <div className="engine-row">
              <div>
                <b>Classic / BM25</b>
                <small>{data?.engines.classic.index ?? "nexus-knowledge-v1"}</small>
              </div>
              <em
                className={
                  data?.engines.classic.status === "healthy" ? "ok" : "bad"
                }
              >
                {data?.engines.classic.status ?? "loading"}
              </em>
            </div>
            <div className="engine-row">
              <div>
                <b>Semantic / HNSW</b>
                <small>
                  {data?.engines.semantic.collection ?? "nexus-knowledge-v1"}
                </small>
              </div>
              <em
                className={
                  data?.engines.semantic.status === "healthy" ? "ok" : "bad"
                }
              >
                {data?.engines.semantic.status ?? "loading"}
              </em>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>Corpus profile</h2>
              <span>11 DOMAINS</span>
            </div>
            <div className="domain-bars">
              {[
                ["Engineering", 82],
                ["SRE", 68],
                ["People", 64],
                ["Security", 51],
                ["Cloud", 47],
                ["IT", 45]
              ].map(([name, width]) => (
                <div className="bar" key={name}>
                  <span>{name}</span>
                  <i style={{ width: `${width}%` }} />
                </div>
              ))}
            </div>
          </article>

          <article className="panel ingestion-panel">
            <div className="panel-head">
              <h2>Index management</h2>
              <span>ADMIN</span>
            </div>
            <p className="panel-copy">
              Index the same canonical EUKB chunks into OpenSearch and Qdrant.
              Only one reindex job can execute in this API process at a time.
            </p>
            <button
              className="admin-action"
              onClick={reindex}
              disabled={jobBusy}
            >
              {jobBusy ? "REINDEXING…" : "REINDEX BOTH ENGINES"}
              <span>↗</span>
            </button>
            <div className="job-status">
              <span>Latest job</span>
              <strong>{job?.state ?? "not started"}</strong>
              {job?.indexed_chunks ? (
                <small>
                  {job.indexed_chunks.toLocaleString()} chunks indexed
                </small>
              ) : null}
              {job?.error ? <small className="bad">{job.error}</small> : null}
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
