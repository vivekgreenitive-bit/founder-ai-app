"""
services/actions_service.py
Extracts concrete action items from diagnosis output and persists them to SQLite.
Bridges: Diagnose → Actions → Outcomes.

This is the core of the "assistant" loop:
  Diagnose output → parse action items → save to DB →
  ActionsScreen lets founder mark done → OutcomeTrackerDB records result →
  Next diagnosis gets outcome context injected into AssessmentAgent.
"""
import sqlite3
import uuid
import time
import re
import json
from typing import Any, Dict, List, Optional

DB_FILE = "conversation_history.db"


class ActionsService:
    """
    Manages the lifecycle of action items generated from diagnosis:
    PENDING → IN_PROGRESS → DONE / PARTIAL / FAILED
    """

    def __init__(self, db_path: str = DB_FILE):
        self._db = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            conn = sqlite3.connect(self._db)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS action_items (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    framework_used TEXT,
                    challenge_summary TEXT,
                    action_text TEXT,
                    action_order INTEGER,
                    status TEXT DEFAULT 'PENDING',
                    outcome_note TEXT,
                    outcome_recorded_at TEXT
                )
            """)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[ActionsService] Schema init error: {e}")

    # ── Parse ─────────────────────────────────────────────────────────────────

    def extract_actions_from_diagnosis(
        self,
        session_id: str,
        diagnosis_text: str,
        framework_used: str = "",
        challenge_summary: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Parses '## 5. Priority Actions' section from structured diagnosis output.
        Falls back to numbered list detection anywhere in the text.
        Returns list of created action dicts.
        """
        action_texts = []

        # Primary: extract from ## 5. Priority Actions section
        section_match = re.search(
            r"##\s*5\.\s*Priority Actions?\s*\n+(.*?)(?:\n##|\Z)",
            diagnosis_text,
            re.DOTALL | re.IGNORECASE,
        )
        if section_match:
            section = section_match.group(1)
            for line in section.splitlines():
                stripped = line.strip()
                # Match numbered items: "1. Do X" or "- Do X"
                m = re.match(r"^(?:\d+[\.\)]\s*|-\s+)(.+)", stripped)
                if m and len(m.group(1)) > 10:
                    action_texts.append(m.group(1).strip())

        # Fallback: scan entire text for numbered lines if section not found
        if not action_texts:
            for line in diagnosis_text.splitlines():
                m = re.match(r"^\d+[\.\)]\s+(.{15,})", line.strip())
                if m:
                    action_texts.append(m.group(1).strip())

        # Limit to 5 most important
        action_texts = action_texts[:5]

        created = []
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            conn = sqlite3.connect(self._db)
            for i, text in enumerate(action_texts):
                item_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO action_items
                    (id, session_id, created_at, updated_at, framework_used,
                     challenge_summary, action_text, action_order, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
                """, (item_id, session_id, ts, ts, framework_used,
                      challenge_summary[:120], text, i + 1))
                created.append({
                    "id": item_id, "session_id": session_id,
                    "action_text": text, "action_order": i + 1,
                    "framework_used": framework_used, "status": "PENDING",
                    "created_at": ts,
                })
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[ActionsService] Insert error: {e}")
        return created

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_all_actions(self) -> List[Dict[str, Any]]:
        """Returns all action items ordered by creation date desc."""
        try:
            conn = sqlite3.connect(self._db)
            rows = conn.execute("""
                SELECT id, session_id, created_at, updated_at, framework_used,
                       challenge_summary, action_text, action_order,
                       status, outcome_note, outcome_recorded_at
                FROM action_items
                ORDER BY created_at DESC, action_order ASC
            """).fetchall()
            conn.close()
            return [self._row_to_dict(r) for r in rows]
        except sqlite3.Error:
            return []

    def get_actions_by_status(self, status: str) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self._db)
            rows = conn.execute("""
                SELECT id, session_id, created_at, updated_at, framework_used,
                       challenge_summary, action_text, action_order,
                       status, outcome_note, outcome_recorded_at
                FROM action_items WHERE status = ?
                ORDER BY created_at DESC, action_order ASC
            """, (status,)).fetchall()
            conn.close()
            return [self._row_to_dict(r) for r in rows]
        except sqlite3.Error:
            return []

    def get_pending_actions_older_than(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Returns PENDING actions created more than N hours ago — for follow-up prompts."""
        try:
            cutoff = time.time() - (hours * 3600)
            conn = sqlite3.connect(self._db)
            rows = conn.execute("""
                SELECT id, session_id, created_at, updated_at, framework_used,
                       challenge_summary, action_text, action_order,
                       status, outcome_note, outcome_recorded_at
                FROM action_items
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
            """).fetchall()
            conn.close()
            results = []
            for r in rows:
                d = self._row_to_dict(r)
                # Parse timestamp and compare
                try:
                    ts_epoch = time.mktime(time.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
                    if ts_epoch < cutoff:
                        results.append(d)
                except Exception:
                    results.append(d)
            return results
        except sqlite3.Error:
            return []

    def get_recent_completed_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns recently completed/failed actions for outcome context injection."""
        try:
            conn = sqlite3.connect(self._db)
            rows = conn.execute("""
                SELECT id, session_id, created_at, updated_at, framework_used,
                       challenge_summary, action_text, action_order,
                       status, outcome_note, outcome_recorded_at
                FROM action_items
                WHERE status IN ('DONE', 'PARTIAL', 'FAILED')
                ORDER BY outcome_recorded_at DESC LIMIT ?
            """, (limit,)).fetchall()
            conn.close()
            return [self._row_to_dict(r) for r in rows]
        except sqlite3.Error:
            return []

    def has_any_actions(self) -> bool:
        return len(self.get_all_actions()) > 0

    # ── Update ────────────────────────────────────────────────────────────────

    def update_status(
        self,
        action_id: str,
        status: str,
        outcome_note: str = "",
    ) -> bool:
        """
        Update action status.
        status: PENDING | IN_PROGRESS | DONE | PARTIAL | FAILED
        """
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            conn = sqlite3.connect(self._db)
            conn.execute("""
                UPDATE action_items
                SET status = ?, outcome_note = ?, updated_at = ?,
                    outcome_recorded_at = CASE WHEN ? IN ('DONE','PARTIAL','FAILED')
                        THEN ? ELSE outcome_recorded_at END
                WHERE id = ?
            """, (status, outcome_note, ts, status, ts, action_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"[ActionsService] Update error: {e}")
            return False

    def build_outcome_context(self) -> str:
        """
        Returns a formatted string of past outcomes for injection into
        AssessmentAgent context. This is what makes the AI learn from execution.
        """
        recent = self.get_recent_completed_actions(limit=5)
        if not recent:
            return ""
        lines = ["Previous execution outcomes (use this to avoid repeating failed approaches):"]
        for a in recent:
            result_emoji = {"DONE": "✓", "PARTIAL": "~", "FAILED": "✗"}.get(a["status"], "?")
            note = f" — {a['outcome_note']}" if a.get("outcome_note") else ""
            lines.append(
                f"  {result_emoji} [{a['framework_used']}] {a['action_text'][:80]}"
                f" → {a['status']}{note}"
            )
        return "\n".join(lines)

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(r) -> Dict[str, Any]:
        keys = ["id", "session_id", "created_at", "updated_at", "framework_used",
                "challenge_summary", "action_text", "action_order",
                "status", "outcome_note", "outcome_recorded_at"]
        return dict(zip(keys, r))
