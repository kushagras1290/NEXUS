import Link from "next/link";
import { KnowledgeField } from "./KnowledgeField";

export function CinematicHome() {
  return (
    <main className="cinema-shell">
      <KnowledgeField />
      <nav className="topbar">
        <Link className="brand" href="/">NEXUS<span className="brand-dot">.</span></Link>
        <div className="top-links"><Link href="/search">Search</Link><Link href="/admin">Admin</Link></div>
      </nav>

      <section className="scene scene-hero">
        <div className="eyebrow">ENTERPRISE KNOWLEDGE / TWO RETRIEVAL ENGINES</div>
        <h1>Knowledge exists<br/>everywhere.</h1>
        <p className="lede">Finding it should not be the difficult part.</p>
        <div className="scroll-cue"><span/>Scroll to converge</div>
      </section>

      <section className="scene scene-domains" aria-label="Knowledge domains">
        <div className="domain-orbit">
          <span>ENGINEERING</span><span>PEOPLE</span><span>SECURITY</span>
          <span>CLOUD</span><span>OPERATIONS</span><span>FINANCE</span>
        </div>
        <div className="scene-copy">
          <div className="eyebrow">ONE CORPUS</div>
          <h2>Fragmented systems.<br/>One focal point.</h2>
          <p>Policies, runbooks, architecture, support knowledge and operational history become one governed retrieval surface.</p>
        </div>
      </section>

      <section className="scene scene-black">
        <p className="whisper">The engine should earn its place.</p>
      </section>

      <section className="scene scene-engine">
        <div className="engine-grid">
          <article><span>01</span><h3>CLASSIC</h3><p>BM25 · inverted indexes · exact identifiers · fuzzy lexical search</p></article>
          <article><span>02</span><h3>SEMANTIC</h3><p>BGE embeddings · Qdrant · HNSW · conceptual similarity</p></article>
          <article><span>03</span><h3>COMPARE</h3><p>Same query. Same ACLs. Same corpus. Measured side by side.</p></article>
        </div>
      </section>

      <section className="scene scene-focal">
        <div className="search-portal">
          <div className="portal-glow" />
          <div className="eyebrow">402,861 SEARCHABLE KNOWLEDGE CHUNKS</div>
          <h2>Ask the organisation.</h2>
          <Link className="primary-cta" href="/search">Enter NEXUS <span>↗</span></Link>
        </div>
      </section>
    </main>
  );
}
