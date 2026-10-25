"""Local, no-cost evidence toolkit for an external research agent.

This program deliberately does not call Ollama, an LLM, or any paid service.
Hermes (or another agent with shell access) uses its commands as guarded tools.
All durable state and downloaded public-source snapshots live under workspace/.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace" / "agent_aid"
DATABASE = WORKSPACE / "factory.sqlite"
EVIDENCE = WORKSPACE / "evidence"
EXPORTS = WORKSPACE / "exports"
USER_AGENT = "GetFranchiseEvidenceFactory/1.0 (+local research tool)"
MAX_DOWNLOAD_BYTES = 2_000_000

GATES = (
    "Direct franchisor confirmation received",
    "Canadian disclosure package obtained",
    "Exact Canadian signing entity confirmed",
    "CAD investment and recurring fees verified",
    "Canadian AUV, EBITDA, or comparable P&L verified",
    "Closure, transfer, resale, and renewal data verified",
    "Current/former franchisee interviews completed",
    "Target-market review, competition, lease, and demographic checks completed",
)
SOURCE_TYPES = {"official", "disclosure", "government", "legal", "directory", "news", "other"}
CLAIM_STATUSES = {"candidate", "verified", "conflicted", "unverified", "rejected"}
CRITICAL_FIELDS = {
    "financials.initial_investment_cad",
    "financials.franchise_fee_cad",
    "financials.royalty_pct",
    "financials.marketing_fee_pct",
    "financials.auv_cad",
}


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower().replace("&", " and ")).strip("-")


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def workspace() -> None:
    for path in (WORKSPACE, EVIDENCE, EXPORTS):
        path.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    workspace()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            brand TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'researching',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL,
            canadian_scope TEXT NOT NULL DEFAULT 'unknown',
            retrieved_at TEXT NOT NULL,
            http_status INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            content_path TEXT NOT NULL,
            UNIQUE(job_id, url)
        );
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            field_id TEXT NOT NULL,
            value TEXT NOT NULL,
            status TEXT NOT NULL,
            primary_source_id INTEGER REFERENCES sources(id),
            supporting_source_id INTEGER REFERENCES sources(id),
            quote TEXT NOT NULL DEFAULT '',
            supporting_quote TEXT NOT NULL DEFAULT '',
            scoring_eligible INTEGER NOT NULL DEFAULT 0,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS gates (
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            result TEXT NOT NULL DEFAULT 'FAIL',
            source_ids TEXT NOT NULL DEFAULT '[]',
            note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY(job_id, name)
        );
        """
    )
    return conn


def row(value: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(value) if value is not None else None


def require_job(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row:
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        raise ValueError(f"job {job_id} does not exist")
    return job


def require_source(conn: sqlite3.Connection, source_id: int, job_id: int | None = None) -> sqlite3.Row:
    source = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not source or (job_id is not None and source["job_id"] != job_id):
        raise ValueError(f"source {source_id} does not exist for this job")
    return source


def update_job(conn: sqlite3.Connection, job_id: int) -> None:
    conn.execute("UPDATE jobs SET updated_at = ? WHERE id = ?", (now(), job_id))


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "br", "li", "h1", "h2", "h3", "tr", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        clean = " ".join(data.split())
        if clean:
            self.parts.append(clean)
            if self._in_title:
                self.title = f"{self.title} {clean}".strip()

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


def safe_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only public http(s) URLs are allowed")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("local network URLs are not allowed")
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise ValueError("private-network URLs are not allowed")
    except ValueError as error:
        if "not allowed" in str(error):
            raise
    if parsed.username or parsed.password:
        raise ValueError("URLs with credentials are not allowed")
    return url


def robot_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except (HTTPError, URLError, OSError):
        # An unavailable robots file is not treated as permission to evade controls;
        # the source fetch itself may still apply its own access rules.
        return True
    return parser.can_fetch(USER_AGENT, url)


def fetch_url(url: str) -> tuple[str, str, int, str]:
    safe_public_url(url)
    if not robot_allowed(url):
        raise ValueError("source robots.txt disallows this research fetch")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,text/plain;q=0.9,*/*;q=0.1"})
    try:
        with urlopen(request, timeout=25) as response:
            data = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(data) > MAX_DOWNLOAD_BYTES:
                raise ValueError(f"source exceeds {MAX_DOWNLOAD_BYTES} byte limit")
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
            final_url = response.geturl()
            status = int(getattr(response, "status", 200))
    except HTTPError as error:
        raise ValueError(f"source fetch failed with HTTP {error.code}") from error
    except URLError as error:
        raise ValueError(f"source fetch failed: {error.reason}") from error
    safe_public_url(final_url)
    if content_type == "text/html":
        parser = TextExtractor()
        parser.feed(data.decode(charset, errors="replace"))
        return final_url, parser.title, status, parser.text()
    if content_type == "text/plain":
        return final_url, "", status, data.decode(charset, errors="replace")
    if content_type == "application/pdf":
        raise ValueError("PDF capture needs a local PDF text extractor; save the public PDF and add extracted text later")
    raise ValueError(f"unsupported source content type: {content_type}")


def create_job(args: argparse.Namespace) -> None:
    brand = " ".join(args.brand.split())
    if not brand:
        raise ValueError("brand cannot be empty")
    conn = connect()
    slug = slugify(brand)
    existing = conn.execute("SELECT * FROM jobs WHERE slug = ?", (slug,)).fetchone()
    if existing:
        emit({"job": row(existing), "created": False})
        return
    timestamp = now()
    cursor = conn.execute("INSERT INTO jobs (brand, slug, created_at, updated_at) VALUES (?, ?, ?, ?)", (brand, slug, timestamp, timestamp))
    job_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO gates (job_id, name, updated_at) VALUES (?, ?, ?)",
        [(job_id, gate, timestamp) for gate in GATES],
    )
    conn.commit()
    emit({"job": row(require_job(conn, job_id)), "created": True, "next": "Run discover or fetch-source, then add-claim."})


def discover(args: argparse.Namespace) -> None:
    query = " ".join(args.query.split())
    if not query:
        raise ValueError("query cannot be empty")
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    _, _, _, document = fetch_url(search_url)
    # The text-only snapshot is not enough to recover result URLs. Fetch this public
    # result page once more to parse anchors, without storing it as franchise evidence.
    request = Request(search_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=25) as response:
        page = response.read(MAX_DOWNLOAD_BYTES).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    links: list[dict[str, str]] = []
    for href, label in re.findall(r'<a[^>]+class="[^\"]*result__a[^\"]*"[^>]+href="([^\"]+)"[^>]*>(.*?)</a>', page, re.IGNORECASE | re.DOTALL):
        parsed = urlparse(html.unescape(href))
        target = parse_qs(parsed.query).get("uddg", [href])[0]
        target = unquote(target)
        if target.startswith("http"):
            links.append({"title": re.sub(r"<.*?>", "", html.unescape(label)).strip(), "url": target})
        if len(links) >= args.limit:
            break
    emit({"query": query, "results": links, "note": "Discovery results are leads, not evidence. Fetch and classify a source before making a claim."})


def fetch_source(args: argparse.Namespace) -> None:
    if args.source_type not in SOURCE_TYPES:
        raise ValueError("invalid source type")
    if args.canadian_scope not in {"yes", "no", "unknown"}:
        raise ValueError("canadian scope must be yes, no, or unknown")
    conn = connect()
    job = require_job(conn, args.job)
    final_url, page_title, http_status, text = fetch_url(args.url)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    safe_name = f"{digest[:16]}.txt"
    evidence_path = EVIDENCE / str(job["id"])
    evidence_path.mkdir(parents=True, exist_ok=True)
    saved = evidence_path / safe_name
    saved.write_text(text + "\n", encoding="utf-8")
    cursor = conn.execute(
        """INSERT INTO sources (job_id, url, title, source_type, canadian_scope, retrieved_at, http_status, content_sha256, content_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(job_id, url) DO UPDATE SET title=excluded.title, source_type=excluded.source_type,
           canadian_scope=excluded.canadian_scope, retrieved_at=excluded.retrieved_at, http_status=excluded.http_status,
           content_sha256=excluded.content_sha256, content_path=excluded.content_path""",
        (job["id"], final_url, args.title or page_title, args.source_type, args.canadian_scope, now(), http_status, digest, str(saved.relative_to(ROOT))),
    )
    source = conn.execute("SELECT * FROM sources WHERE job_id = ? AND url = ?", (job["id"], final_url)).fetchone()
    update_job(conn, job["id"])
    conn.commit()
    emit({"source": row(source), "bytes_saved": saved.stat().st_size, "note": "Read the saved evidence file and quote the supporting passage when adding a claim."})


def add_claim(args: argparse.Namespace) -> None:
    if args.status not in {"candidate", "unverified", "rejected"}:
        raise ValueError("new claims must start as candidate, unverified, or rejected")
    conn = connect()
    require_job(conn, args.job)
    source_id = args.source
    if args.status == "candidate" and not source_id:
        raise ValueError("a candidate claim needs a primary source")
    if source_id:
        require_source(conn, source_id, args.job)
    if args.status == "candidate" and not args.quote.strip():
        raise ValueError("a candidate claim needs a supporting quote")
    timestamp = now()
    cursor = conn.execute(
        """INSERT INTO claims (job_id, field_id, value, status, primary_source_id, quote, scoring_eligible, note, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (args.job, args.field, args.value, args.status, source_id, args.quote.strip(), int(args.scoring_eligible), args.note.strip(), timestamp, timestamp),
    )
    update_job(conn, args.job)
    conn.commit()
    claim = conn.execute("SELECT * FROM claims WHERE id = ?", (cursor.lastrowid,)).fetchone()
    emit({"claim": row(claim), "next": "Use verify-claim with a different-domain source before treating a critical claim as verified."})


def verify_claim(args: argparse.Namespace) -> None:
    conn = connect()
    claim = conn.execute("SELECT * FROM claims WHERE id = ?", (args.claim,)).fetchone()
    if not claim:
        raise ValueError(f"claim {args.claim} does not exist")
    if claim["status"] != "candidate":
        raise ValueError("only candidate claims can be verified")
    primary = require_source(conn, int(claim["primary_source_id"]), claim["job_id"])
    supporting = require_source(conn, args.source, claim["job_id"])
    if urlparse(primary["url"]).hostname.lower() == urlparse(supporting["url"]).hostname.lower():
        raise ValueError("verification requires an independent source domain")
    if not args.quote.strip():
        raise ValueError("verification needs a supporting quote")
    conn.execute(
        "UPDATE claims SET status = 'verified', supporting_source_id = ?, supporting_quote = ?, updated_at = ? WHERE id = ?",
        (supporting["id"], args.quote.strip(), now(), claim["id"]),
    )
    update_job(conn, claim["job_id"])
    conn.commit()
    emit({"claim": row(conn.execute("SELECT * FROM claims WHERE id = ?", (claim["id"],)).fetchone()), "verified": True})


def mark_conflict(args: argparse.Namespace) -> None:
    conn = connect()
    require_job(conn, args.job)
    changed = conn.execute(
        "UPDATE claims SET status = 'conflicted', note = ?, updated_at = ? WHERE job_id = ? AND field_id = ? AND status IN ('candidate', 'verified')",
        (args.note.strip() or "Conflicting public claims require franchisor confirmation.", now(), args.job, args.field),
    ).rowcount
    update_job(conn, args.job)
    conn.commit()
    emit({"job_id": args.job, "field_id": args.field, "claims_marked_conflicted": changed})


def set_gate(args: argparse.Namespace) -> None:
    if args.name not in GATES:
        raise ValueError("gate name must match one of the eight fixed evidence gates")
    conn = connect()
    require_job(conn, args.job)
    source_ids = sorted(set(args.sources or []))
    if args.result == "PASS" and not source_ids:
        raise ValueError("a PASS gate requires at least one linked source")
    for source_id in source_ids:
        require_source(conn, source_id, args.job)
    conn.execute(
        "UPDATE gates SET result = ?, source_ids = ?, note = ?, updated_at = ? WHERE job_id = ? AND name = ?",
        (args.result, json.dumps(source_ids), args.note.strip(), now(), args.job, args.name),
    )
    update_job(conn, args.job)
    conn.commit()
    emit({"job_id": args.job, "gate": args.name, "result": args.result, "source_ids": source_ids})


def audit_job(conn: sqlite3.Connection, job_id: int) -> dict[str, Any]:
    job = require_job(conn, job_id)
    sources = conn.execute("SELECT * FROM sources WHERE job_id = ? ORDER BY id", (job_id,)).fetchall()
    claims = conn.execute("SELECT * FROM claims WHERE job_id = ? ORDER BY field_id, id", (job_id,)).fetchall()
    gates = conn.execute("SELECT * FROM gates WHERE job_id = ? ORDER BY name", (job_id,)).fetchall()
    issues: list[dict[str, Any]] = []
    source_ids = {source["id"] for source in sources}
    for claim in claims:
        if claim["status"] in {"candidate", "verified"} and (not claim["primary_source_id"] or not claim["quote"].strip()):
            issues.append({"kind": "claim_missing_primary_evidence", "claim_id": claim["id"], "field_id": claim["field_id"]})
        if claim["status"] == "verified" and not claim["supporting_source_id"]:
            issues.append({"kind": "verified_claim_missing_second_source", "claim_id": claim["id"], "field_id": claim["field_id"]})
        if claim["status"] == "verified" and claim["field_id"] in CRITICAL_FIELDS and not claim["scoring_eligible"]:
            issues.append({"kind": "verified_critical_claim_not_marked_for_scoring", "claim_id": claim["id"], "field_id": claim["field_id"]})
    for gate in gates:
        ids = json.loads(gate["source_ids"])
        if gate["result"] == "PASS" and (not ids or any(source_id not in source_ids for source_id in ids)):
            issues.append({"kind": "gate_missing_linked_evidence", "gate": gate["name"]})
    values_by_field: dict[str, set[str]] = {}
    for claim in claims:
        if claim["status"] == "verified":
            values_by_field.setdefault(claim["field_id"], set()).add(claim["value"])
    for field_id, values in values_by_field.items():
        if len(values) > 1:
            issues.append({"kind": "unresolved_verified_conflict", "field_id": field_id, "values": sorted(values)})
    all_gates_pass = len(gates) == len(GATES) and all(gate["result"] == "PASS" for gate in gates)
    return {
        "job": row(job),
        "source_count": len(sources),
        "claim_counts": {status: sum(claim["status"] == status for claim in claims) for status in sorted(CLAIM_STATUSES)},
        "gates_passed": sum(gate["result"] == "PASS" for gate in gates),
        "gates_total": len(GATES),
        "profile_status": "investor_ready" if all_gates_pass and not issues else "screening_profile",
        "issues": issues,
        "audit_ready": not issues,
    }


def audit(args: argparse.Namespace) -> None:
    conn = connect()
    emit(audit_job(conn, args.job))


def show_job(args: argparse.Namespace) -> None:
    conn = connect()
    job = require_job(conn, args.job)
    sources = [row(item) for item in conn.execute("SELECT * FROM sources WHERE job_id = ? ORDER BY id", (args.job,))]
    claims = [row(item) for item in conn.execute("SELECT * FROM claims WHERE job_id = ? ORDER BY field_id, id", (args.job,))]
    gates = [row(item) for item in conn.execute("SELECT * FROM gates WHERE job_id = ? ORDER BY name", (args.job,))]
    emit({"job": row(job), "sources": sources, "claims": claims, "gates": gates, "audit": audit_job(conn, args.job)})


def export_job(args: argparse.Namespace) -> None:
    conn = connect()
    audit = audit_job(conn, args.job)
    job = require_job(conn, args.job)
    sources = [row(item) for item in conn.execute("SELECT * FROM sources WHERE job_id = ? ORDER BY id", (args.job,))]
    claims = [row(item) for item in conn.execute("SELECT * FROM claims WHERE job_id = ? ORDER BY field_id, id", (args.job,))]
    gates = [row(item) for item in conn.execute("SELECT * FROM gates WHERE job_id = ? ORDER BY name", (args.job,))]
    document = {"schema_version": "2.0", "job": row(job), "audit": audit, "sources": sources, "claims": claims, "evidence_gates": gates}
    path = EXPORTS / f"{job['slug']}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    emit({"export": str(path.relative_to(ROOT)), "profile_status": audit["profile_status"], "audit_ready": audit["audit_ready"]})


def parser() -> argparse.ArgumentParser:
    app = argparse.ArgumentParser(description="Evidence factory tools for an external local research agent. No model calls.")
    commands = app.add_subparsers(dest="command", required=True)

    command = commands.add_parser("create-job", help="Create or reopen a franchise research job.")
    command.add_argument("brand")
    command.set_defaults(func=create_job)

    command = commands.add_parser("discover", help="Find public web leads. Leads are not evidence.")
    command.add_argument("query")
    command.add_argument("--limit", type=int, default=8)
    command.set_defaults(func=discover)

    command = commands.add_parser("fetch-source", help="Fetch and archive a public HTML or text source.")
    command.add_argument("--job", type=int, required=True)
    command.add_argument("--url", required=True)
    command.add_argument("--source-type", choices=sorted(SOURCE_TYPES), required=True)
    command.add_argument("--canadian-scope", choices=("yes", "no", "unknown"), default="unknown")
    command.add_argument("--title", default="")
    command.set_defaults(func=fetch_source)

    command = commands.add_parser("add-claim", help="Record a field-level claim. New claims cannot be marked verified.")
    command.add_argument("--job", type=int, required=True)
    command.add_argument("--field", required=True)
    command.add_argument("--value", required=True)
    command.add_argument("--status", choices=("candidate", "unverified", "rejected"), default="candidate")
    command.add_argument("--source", type=int)
    command.add_argument("--quote", default="")
    command.add_argument("--note", default="")
    command.add_argument("--scoring-eligible", action="store_true")
    command.set_defaults(func=add_claim)

    command = commands.add_parser("verify-claim", help="Promote a candidate using a different-domain supporting source.")
    command.add_argument("--claim", type=int, required=True)
    command.add_argument("--source", type=int, required=True)
    command.add_argument("--quote", required=True)
    command.set_defaults(func=verify_claim)

    command = commands.add_parser("mark-conflict", help="Mark competing claims for one field as conflicted.")
    command.add_argument("--job", type=int, required=True)
    command.add_argument("--field", required=True)
    command.add_argument("--note", default="")
    command.set_defaults(func=mark_conflict)

    command = commands.add_parser("set-gate", help="Set an evidence gate; PASS requires linked source IDs.")
    command.add_argument("--job", type=int, required=True)
    command.add_argument("--name", required=True)
    command.add_argument("--result", choices=("PASS", "FAIL"), required=True)
    command.add_argument("--sources", type=int, nargs="*")
    command.add_argument("--note", default="")
    command.set_defaults(func=set_gate)

    command = commands.add_parser("audit", help="Run deterministic evidence-policy checks.")
    command.add_argument("--job", type=int, required=True)
    command.set_defaults(func=audit)

    command = commands.add_parser("show-job", help="Show all saved work for a job.")
    command.add_argument("--job", type=int, required=True)
    command.set_defaults(func=show_job)

    command = commands.add_parser("export", help="Export a safe profile record; this never changes the website.")
    command.add_argument("--job", type=int, required=True)
    command.set_defaults(func=export_job)
    return app


def main() -> None:
    args = parser().parse_args()
    try:
        args.func(args)
    except (ValueError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
