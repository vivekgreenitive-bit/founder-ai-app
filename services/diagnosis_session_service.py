"""
services/diagnosis_session_service.py
Persists the most recent diagnosis result to SQLite so TodayScreen can display
real constraint cards without requiring the user to re-run analysis each session.
"""
import sqlite3
import json
import time
import os
from typing import Any, Dict, List, Optional

DB_FILE = "conversation_history.db"


class DiagnosisSessionService:
    """
    Stores and retrieves persisted diagnosis sessions.
    TodayScreen reads from this to populate "Needs Your Attention" cards with real data.
    """

    def __init__(self, db_path: str = DB_FILE):
        self._db = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            conn = sqlite3.connect(self._db)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS diagnosis_sessions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    query TEXT,
                    framework_used TEXT,
                    constraint_name TEXT,
                    confidence_score REAL,
                    evidence_count INTEGER,
                    priority TEXT,
                    full_result TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[DiagnosisSessionService] Schema init error: {e}")

    def save_session(
        self,
        session_id: str,
        query: str,
        framework_used: str,
        constraint_name: str,
        confidence_score: float,
        evidence_count: int,
        full_result: str,
        priority: str = "HIGH",
    ) -> None:
        try:
            conn = sqlite3.connect(self._db)
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            conn.execute("""
                INSERT OR REPLACE INTO diagnosis_sessions
                (id, timestamp, query, framework_used, constraint_name,
                 confidence_score, evidence_count, priority, full_result, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (session_id, ts, query[:200], framework_used,
                  constraint_name, confidence_score, evidence_count,
                  priority, full_result))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[DiagnosisSessionService] Save error: {e}")

    def get_recent_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns most recent diagnosis sessions for TodayScreen command center."""
        try:
            conn = sqlite3.connect(self._db)
            rows = conn.execute("""
                SELECT id, timestamp, query, framework_used, constraint_name,
                       confidence_score, evidence_count, priority, status
                FROM diagnosis_sessions
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
            conn.close()
            return [
                {
                    "id": r[0], "timestamp": r[1], "query": r[2],
                    "framework": r[3], "constraint": r[4],
                    "confidence": r[5], "evidence_count": r[6],
                    "priority": r[7], "status": r[8],
                }
                for r in rows
            ]
        except sqlite3.Error:
            return []

    def get_session_result(self, session_id: str) -> Optional[str]:
        """Returns full diagnosis text for a given session ID."""
        try:
            conn = sqlite3.connect(self._db)
            row = conn.execute(
                "SELECT full_result FROM diagnosis_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            conn.close()
            return row[0] if row else None
        except sqlite3.Error:
            return None

    def has_any_sessions(self) -> bool:
        return len(self.get_recent_sessions(limit=1)) > 0
