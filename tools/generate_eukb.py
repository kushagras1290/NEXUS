#!/usr/bin/env python3
"""Generate NEXUS EUKB v1: a deterministic synthetic enterprise corpus.

No confidential corporate data is used. The default build emits exactly:
- 50,000 source documents
- 402,861 search chunks
- 5,000 labelled evaluation queries

The query set intentionally covers semantic paraphrase, exact terminology, identifiers,
acronyms, typos, multi-condition requests, ambiguity, policy-version conflicts,
cross-domain retrieval and permission-sensitive cases.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SEED = 20260923
DEFAULT_DOCUMENTS = 50_000
DEFAULT_EVAL_QUERIES = 5_000
DEFAULT_CHUNKS = 402_861

DOMAIN_COUNTS = {
    "Software Engineering": 10_000,
    "DevOps & SRE": 7_000,
    "Cloud": 4_000,
    "Cybersecurity": 4_000,
    "Human Resources": 7_000,
    "IT Support": 5_000,
    "Project Delivery": 3_500,
    "Finance & Benefits": 2_500,
    "Compliance & Legal": 2_000,
    "Learning & Development": 2_000,
    "Organisation & Directory": 3_000,
}

TOPICS = {
    "Software Engineering": [
        "FastAPI service standard", "REST versioning", "PostgreSQL indexing",
        "Kafka event design", "React standards", "dependency pinning",
        "API idempotency", "contract testing", "database migration safety",
    ],
    "DevOps & SRE": [
        "connection pool exhaustion", "HTTP 503 spike", "Kubernetes rollback",
        "certificate expiry", "SLOs", "queue backlog", "replication lag",
        "emergency release", "node pressure",
    ],
    "Cloud": [
        "approved regions", "data residency", "IAM roles", "landing zones",
        "cost controls", "RDS deployment", "EKS baseline", "budget alerts",
    ],
    "Cybersecurity": [
        "MFA", "privileged access", "secret rotation", "PII handling",
        "phishing response", "service accounts", "dependency scanning",
        "credential compromise",
    ],
    "Human Resources": [
        "annual leave", "work from home", "probation", "maternity leave",
        "notice period", "leave carry forward", "health insurance",
        "performance review", "employee referrals",
    ],
    "IT Support": [
        "MFA reset", "password reset", "VPN", "laptop replacement",
        "Docker installation", "account lockout", "new phone enrollment",
        "email setup", "admin privileges",
    ],
    "Project Delivery": [
        "release readiness", "change control", "UAT", "risk register",
        "definition of done", "design review", "project closure",
    ],
    "Finance & Benefits": [
        "travel reimbursement", "software procurement", "salary cycle",
        "tax declarations", "expense deadlines", "vendor onboarding",
        "payroll corrections",
    ],
    "Compliance & Legal": [
        "GDPR handling", "NDA", "retention", "cross-border transfer",
        "litigation hold", "SOW approval", "secure disposal",
    ],
    "Learning & Development": [
        "Python learning path", "cloud certification", "security training",
        "new manager training", "privacy training", "Kubernetes learning path",
    ],
    "Organisation & Directory": [
        "service owner", "SEV1 contacts", "security escalation",
        "platform engineering", "data owner", "product owner",
        "HR escalation",
    ],
}

PREFIXES = {
    "Software Engineering": "ENG", "DevOps & SRE": "SRE", "Cloud": "CLD",
    "Cybersecurity": "SEC", "Human Resources": "HR", "IT Support": "ITS",
    "Project Delivery": "PMO", "Finance & Benefits": "FIN",
    "Compliance & Legal": "LEG", "Learning & Development": "LND",
    "Organisation & Directory": "ORG",
}
COUNTRIES = ["GLOBAL", "IN", "UK", "IE", "US", "SG", "AU"]
SOURCE_SYSTEMS = ["confluence", "sharepoint", "google_drive", "github", "servicenow", "hr_portal"]
ROLE_SETS = {
    "Software Engineering": ["employee", "engineer", "tech_lead", "architect"],
    "DevOps & SRE": ["employee", "engineer", "sre", "tech_lead"],
    "Cloud": ["employee", "engineer", "cloud_engineer", "architect"],
    "Cybersecurity": ["employee", "engineer", "security", "manager"],
    "Human Resources": ["employee", "manager", "hr"],
    "IT Support": ["employee", "manager", "it_support"],
    "Project Delivery": ["employee", "engineer", "project_manager", "manager"],
    "Finance & Benefits": ["employee", "manager", "finance"],
    "Compliance & Legal": ["employee", "manager", "legal", "compliance"],
    "Learning & Development": ["employee", "manager", "hr"],
    "Organisation & Directory": ["employee", "manager"],
}

SYNONYMS = {
    "work from home": ["WFH", "remote work", "remote working", "telecommuting"],
    "Kubernetes": ["K8s", "kube"],
    "Identity and Access Management": ["IAM", "identity access management"],
    "multi-factor authentication": ["MFA", "2FA", "two-factor authentication"],
    "paid time off": ["PTO", "annual leave", "vacation leave"],
    "continuous integration": ["CI", "CI/CD", "build pipeline"],
    "continuous delivery": ["CD", "deployment pipeline", "release pipeline"],
    "site reliability engineering": ["SRE", "production engineering"],
    "pull request": ["PR", "merge request"],
    "database": ["DB", "data store"],
    "Amazon Web Services": ["AWS"],
    "single sign-on": ["SSO"],
    "personal identifiable information": ["PII", "personal data"],
    "service level objective": ["SLO"],
}

SEMANTIC_QUERIES = {
    "work from home": "How often can I perform my job away from the office?",
    "annual leave": "How much vacation time do employees receive?",
    "leave carry forward": "Can unused vacation days move into the next year?",
    "probation": "What rules apply during my first months before confirmation?",
    "MFA reset": "I replaced my phone and can no longer approve sign-in prompts. What do I do?",
    "new phone enrollment": "How do I register a replacement mobile device for account verification?",
    "connection pool exhaustion": "The service slows down under traffic and database sessions appear stuck. What should we check?",
    "HTTP 503 spike": "Users suddenly see service unavailable responses after traffic increases.",
    "approved regions": "Which geographic locations are allowed to host customer workloads?",
    "data residency": "Can customer information be stored in another country?",
    "FastAPI service standard": "What baseline requirements apply to a new Python web API?",
    "REST versioning": "What should we do when an API change would break existing clients?",
    "travel reimbursement": "How do I get paid back for costs from a business trip?",
    "emergency release": "The standard deployment path is broken but production needs an urgent fix. What is the approved procedure?",
    "privileged access": "How do I obtain temporary elevated permissions for an administrative task?",
}

QUERY_DISTRIBUTION = [
    ("semantic_paraphrase", 1_000),
    ("exact_terminology", 800),
    ("identifier_error_code", 500),
    ("acronym", 500),
    ("typo_fuzzy", 500),
    ("multi_condition", 500),
    ("ambiguous", 400),
    ("policy_version", 400),
    ("cross_domain", 200),
    ("permission_sensitive", 200),
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def sha(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def write_jsonl_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def document_sections(title: str, topic: str, domain: str, country: str, owner: str, version: str, status: str, extra: bool) -> list[tuple[str, str]]:
    sections = [
        ("Document", f"# {title}"),
        ("Purpose", f"This document defines the approved operating model for {topic} within the fictional NEXUS enterprise corpus."),
        ("Scope", f"It applies to relevant {domain} workflows for {country}. Country-specific controls override the global baseline when explicitly documented."),
        ("Requirements", f"Teams working with {topic} must verify the current policy version, use approved tooling, preserve traceable evidence, and apply least privilege."),
        ("Controls", "Elevated access and production-impacting changes require explicit approval. Sensitive information follows the organisation classification model."),
        ("Procedure", f"Confirm the request concerns {topic}; identify owner, environment and jurisdiction; follow the approved workflow; escalate unresolved exceptions to {owner}."),
        ("Validation", "Verify the current document version before acting. Record identifiers, timestamps, evidence and rollback details when operational changes are involved."),
        ("Version", f"Version {version}. Status: {status}. Archived versions are retained for audit but must not guide new decisions."),
    ]
    if extra:
        sections.append(("Related References", f"Related knowledge may include {domain} standards, owner directories, incident history and service documentation connected to {topic}."))
    return sections


def build_corpus(document_target: int, chunk_target: int, rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if document_target != DEFAULT_DOCUMENTS:
        scaled = {domain: max(1, round(count * document_target / DEFAULT_DOCUMENTS)) for domain, count in DOMAIN_COUNTS.items()}
        difference = document_target - sum(scaled.values())
        scaled[next(iter(scaled))] += difference
        counts = scaled
        base_chunks = 8 * document_target
        chunk_target = max(base_chunks, round(DEFAULT_CHUNKS * document_target / DEFAULT_DOCUMENTS))
    else:
        counts = DOMAIN_COUNTS

    extra_chunks = max(0, chunk_target - 8 * document_target)
    documents: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    global_index = 0
    series_last: dict[tuple[str, str, str], str] = {}

    for domain, count in counts.items():
        for local_index in range(count):
            global_index += 1
            topic = rng.choice(TOPICS[domain])
            prefix = PREFIXES[domain]
            country = rng.choices(COUNTRIES, weights=[42, 16, 11, 6, 12, 7, 6])[0]
            version = f"{1 + (local_index % 5)}.{rng.randint(0, 4)}"
            status = rng.choices(["ACTIVE", "ARCHIVED", "DRAFT"], weights=[73, 24, 3])[0]
            classification = rng.choices(["INTERNAL", "EMPLOYEE", "CONFIDENTIAL"], weights=[70, 24, 6])[0]
            owner = f"{domain} Knowledge Team"
            doc_id = f"{prefix}-{global_index:06d}"
            series_key = (domain, topic, country)
            previous = series_last.get(series_key)
            if status == "ACTIVE":
                series_last[series_key] = doc_id
            error_code = None
            if domain in {"DevOps & SRE", "IT Support", "Cybersecurity"} and rng.random() < 0.20:
                error_code = f"ERR-{prefix}-{rng.randint(1000, 9999)}"
            title = f"{topic.title()} — {country}"
            roles = ROLE_SETS[domain]
            if classification == "CONFIDENTIAL":
                privileged = [r for r in roles if r != "employee"] or roles
                allowed_roles = privileged
                allowed_departments = [domain]
            else:
                allowed_roles = roles
                allowed_departments = []
            extra = global_index <= extra_chunks
            sections = document_sections(title, topic, domain, country, owner, version, status, extra)
            content = "\n\n".join(f"## {heading}\n{text}" if heading != "Document" else text for heading, text in sections)
            if error_code:
                content += f"\n\nReference identifier: {error_code}."
            doc = {
                "document_id": doc_id,
                "series_id": f"{prefix}-{slug(topic)[:16]}-{slug(country)}",
                "previous_version_id": previous,
                "title": title,
                "content": content,
                "department": domain,
                "business_unit": rng.choice(["Enterprise Platforms", "Digital Delivery", "Corporate Functions", "Cloud & Security", "Shared Services"]),
                "category": domain,
                "subcategory": topic,
                "document_type": "policy" if domain == "Human Resources" else ("runbook" if domain == "DevOps & SRE" else "knowledge_article"),
                "author": owner,
                "owner_team": owner,
                "country": country,
                "region": country,
                "language": "en",
                "tags": sorted({slug(topic), slug(domain), prefix.lower()}),
                "keywords": [topic, domain],
                "classification": classification,
                "allowed_roles": allowed_roles,
                "allowed_departments": allowed_departments,
                "source_system": rng.choice(SOURCE_SYSTEMS),
                "source_uri": f"synthetic://{slug(domain)}/{doc_id}",
                "version": version,
                "created_at": f"202{3 + (global_index % 4)}-{1 + (global_index % 12):02d}-{1 + (global_index % 27):02d}",
                "updated_at": "2026-09-23",
                "effective_at": "2026-01-01",
                "expires_at": None,
                "status": status,
                "synthetic": True,
                "source_license": "Synthetic research/demo corpus",
                "validation_status": "VALIDATED",
                "error_code": error_code,
                "content_hash": sha(content),
            }
            documents.append(doc)
            for ci, (heading, text) in enumerate(sections):
                chunk_text = f"{title}\n{heading}\n{text}"
                chunks.append({
                    "chunk_id": f"{doc_id}-C{ci:02d}",
                    "document_id": doc_id,
                    "series_id": doc["series_id"],
                    "chunk_index": ci,
                    "section": heading,
                    "text": chunk_text,
                    "department": domain,
                    "category": domain,
                    "subcategory": topic,
                    "document_type": doc["document_type"],
                    "country": country,
                    "classification": classification,
                    "allowed_roles": allowed_roles,
                    "allowed_departments": allowed_departments,
                    "version": version,
                    "status": status,
                    "owner_team": owner,
                    "source_system": doc["source_system"],
                    "updated_at": "2026-09-23",
                    "content_hash": sha(chunk_text),
                })
    return documents, chunks


def typo(value: str) -> str:
    words = value.split()
    if not words:
        return value
    index = max(range(len(words)), key=lambda i: len(words[i]))
    word = words[index]
    if len(word) > 4:
        p = len(word) // 2
        word = word[:p-1] + word[p] + word[p-1] + word[p+1:]
    words[index] = word
    return " ".join(words)


def build_queries(documents: list[dict[str, Any]], target: int, rng: random.Random) -> list[dict[str, Any]]:
    active = [d for d in documents if d["status"] == "ACTIVE"]
    confidential = [d for d in active if d["classification"] == "CONFIDENTIAL"]
    identifier_docs = [d for d in active if d.get("error_code")]
    versioned = [d for d in active if d.get("previous_version_id")]
    by_topic: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for d in active:
        by_topic[(d["department"], d["subcategory"], d["country"])].append(d)

    if target == DEFAULT_EVAL_QUERIES:
        distribution = QUERY_DISTRIBUTION
    else:
        names = [name for name, _ in QUERY_DISTRIBUTION]
        distribution = [(name, target // len(names)) for name in names]
        distribution[0] = (distribution[0][0], distribution[0][1] + target - sum(n for _, n in distribution))

    queries: list[dict[str, Any]] = []
    qid = 0
    for query_type, count in distribution:
        for _ in range(count):
            qid += 1
            if query_type == "permission_sensitive":
                d = rng.choice(confidential)
            elif query_type == "identifier_error_code":
                d = rng.choice(identifier_docs)
            elif query_type == "policy_version":
                d = rng.choice(versioned or active)
            else:
                d = rng.choice(active)

            if query_type == "semantic_paraphrase":
                query = SEMANTIC_QUERIES.get(d["subcategory"], f"What is the approved company procedure for this {str(d['category']).lower()} situation?")
            elif query_type == "exact_terminology":
                query = f"{d['subcategory']} {d['country']}"
            elif query_type == "identifier_error_code":
                query = str(d.get("error_code") or d["document_id"])
            elif query_type == "acronym":
                acronym = next((vals[0] for key, vals in SYNONYMS.items() if key.lower() in str(d["subcategory"]).lower()), str(d["subcategory"]).split()[0].upper())
                query = f"{acronym} policy"
            elif query_type == "typo_fuzzy":
                query = typo(str(d["subcategory"]))
            elif query_type == "multi_condition":
                query = f"{d['subcategory']} for {d['country']} {str(d['classification']).lower()} users"
            elif query_type == "ambiguous":
                query = str(d["subcategory"]).split()[0].lower() + " issue"
            elif query_type == "policy_version":
                query = f"current {d['subcategory']} policy {d['country']}"
            elif query_type == "cross_domain":
                other = rng.choice([x for x in active if x["department"] != d["department"]])
                query = f"Find guidance connecting {d['subcategory']} with {other['subcategory']}"
            else:
                query = f"{d['subcategory']} confidential procedure"

            relevance = [{"document_id": d["document_id"], "grade": 3}]
            for related in by_topic[(d["department"], d["subcategory"], d["country"])]:
                if related["document_id"] != d["document_id"] and len(relevance) < 3:
                    relevance.append({"document_id": related["document_id"], "grade": 2})
            if query_type == "policy_version" and d.get("previous_version_id"):
                relevance.append({"document_id": d["previous_version_id"], "grade": 0})

            queries.append({
                "query_id": f"Q-{qid:05d}",
                "query": query,
                "query_type": query_type,
                "user_country": d["country"],
                "user_department": d["department"] if d["classification"] == "CONFIDENTIAL" else rng.choice(list(DOMAIN_COUNTS)),
                "user_role": rng.choice(d["allowed_roles"]),
                "target_department": d["department"],
                "target_category": d["category"],
                "target_subcategory": d["subcategory"],
                "relevance_judgments": relevance,
            })
    return queries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--documents", type=int, default=DEFAULT_DOCUMENTS)
    parser.add_argument("--eval-queries", type=int, default=DEFAULT_EVAL_QUERIES)
    args = parser.parse_args()
    if args.documents < 100 or args.eval_queries < 10:
        raise SystemExit("Use at least 100 documents and 10 evaluation queries")

    rng = random.Random(SEED)
    chunk_target = DEFAULT_CHUNKS if args.documents == DEFAULT_DOCUMENTS else round(DEFAULT_CHUNKS * args.documents / DEFAULT_DOCUMENTS)
    documents, chunks = build_corpus(args.documents, chunk_target, rng)
    queries = build_queries(documents, args.eval_queries, rng)

    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl_gz(args.output / "documents.jsonl.gz", documents)
    write_jsonl_gz(args.output / "chunks.jsonl.gz", chunks)
    write_jsonl_gz(args.output / "evaluation_queries.jsonl.gz", queries)

    query_counts: dict[str, int] = defaultdict(int)
    for item in queries:
        query_counts[item["query_type"]] += 1
    manifest = {
        "dataset_name": "NEXUS Enterprise Unified Knowledge Base (EUKB) v1",
        "company_is_fictional": True,
        "seed": SEED,
        "documents": len(documents),
        "chunks": len(chunks),
        "evaluation_queries": len(queries),
        "domain_counts": DOMAIN_COUNTS if args.documents == DEFAULT_DOCUMENTS else "scaled",
        "query_type_counts": dict(query_counts),
        "synthetic": True,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (args.output / "synonyms.json").write_text(json.dumps(SYNONYMS, indent=2), encoding="utf-8")
    taxonomy = {domain: {"topics": topics, "roles": ROLE_SETS[domain]} for domain, topics in TOPICS.items()}
    (args.output / "taxonomy.json").write_text(json.dumps(taxonomy, indent=2), encoding="utf-8")
    document_ids = {str(d["document_id"]) for d in documents}
    invalid_chunk_parents = sum(1 for c in chunks if str(c["document_id"]) not in document_ids)
    invalid_eval_refs = sum(1 for q in queries for j in q["relevance_judgments"] if str(j["document_id"]) not in document_ids)
    validation = {
        "document_ids_unique": len(document_ids) == len(documents),
        "all_chunks_have_valid_parent": invalid_chunk_parents == 0,
        "all_eval_refs_resolve": invalid_eval_refs == 0,
        "documents": len(documents),
        "chunks": len(chunks),
        "evaluation_queries": len(queries),
        "query_type_counts": dict(query_counts),
    }
    (args.output / "validation_report.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
