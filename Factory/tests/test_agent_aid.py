from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "agent_aid.py"
SPEC = importlib.util.spec_from_file_location("agent_aid", MODULE_PATH)
assert SPEC and SPEC.loader
agent_aid = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_aid)


class AgentAidTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.connections = []
        root = Path(self.temp.name)
        self.original = (agent_aid.WORKSPACE, agent_aid.DATABASE, agent_aid.EVIDENCE, agent_aid.EXPORTS)
        agent_aid.WORKSPACE = root / "workspace"
        agent_aid.DATABASE = agent_aid.WORKSPACE / "factory.sqlite"
        agent_aid.EVIDENCE = agent_aid.WORKSPACE / "evidence"
        agent_aid.EXPORTS = agent_aid.WORKSPACE / "exports"

    def tearDown(self) -> None:
        for conn in self.connections:
            conn.close()
        agent_aid.WORKSPACE, agent_aid.DATABASE, agent_aid.EVIDENCE, agent_aid.EXPORTS = self.original
        self.temp.cleanup()

    def _job(self) -> tuple[object, int]:
        conn = agent_aid.connect()
        self.connections.append(conn)
        timestamp = agent_aid.now()
        cursor = conn.execute("INSERT INTO jobs (brand, slug, created_at, updated_at) VALUES (?, ?, ?, ?)", ("Test Brand", "test-brand", timestamp, timestamp))
        job_id = cursor.lastrowid
        conn.executemany("INSERT INTO gates (job_id, name, updated_at) VALUES (?, ?, ?)", [(job_id, gate, timestamp) for gate in agent_aid.GATES])
        conn.commit()
        return conn, job_id

    def _source(self, conn: object, job_id: int, url: str) -> int:
        cursor = conn.execute(
            "INSERT INTO sources (job_id, url, source_type, retrieved_at, http_status, content_sha256, content_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, url, "official", agent_aid.now(), 200, "a" * 64, "evidence/test.txt"),
        )
        conn.commit()
        return cursor.lastrowid

    def test_verified_claim_needs_a_second_source(self) -> None:
        conn, job_id = self._job()
        first = self._source(conn, job_id, "https://official.example/terms")
        cursor = conn.execute(
            "INSERT INTO claims (job_id, field_id, value, status, primary_source_id, quote, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, "financials.royalty_pct", "6", "verified", first, "Royalty is 6%", agent_aid.now(), agent_aid.now()),
        )
        conn.commit()
        audit = agent_aid.audit_job(conn, job_id)
        self.assertTrue(any(issue["kind"] == "verified_claim_missing_second_source" for issue in audit["issues"]))
        self.assertEqual(cursor.lastrowid, 1)

    def test_private_urls_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "private-network"):
            agent_aid.safe_public_url("http://127.0.0.1/private")

    def test_all_passed_gates_need_evidence(self) -> None:
        conn, job_id = self._job()
        conn.execute("UPDATE gates SET result = 'PASS' WHERE job_id = ?", (job_id,))
        conn.commit()
        audit = agent_aid.audit_job(conn, job_id)
        self.assertEqual(audit["profile_status"], "screening_profile")
        self.assertEqual(sum(issue["kind"] == "gate_missing_linked_evidence" for issue in audit["issues"]), 8)


if __name__ == "__main__":
    unittest.main()
