import sqlite3
import os
import time
import json
from typing import Dict, Any, List

class OutcomeTrackerDB:
    """
    Manages persistent decision tracking, experiment baseline vs actuals, 
    and outcome-based framework learning history.
    """
    def __init__(self, db_path: str = "conversation_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_outcomes (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                framework_selected TEXT,
                problem_statement TEXT,
                target_metric_name TEXT,
                baseline_value REAL,
                target_value REAL,
                actual_value REAL,
                status TEXT,
                arr_impact REAL
            )
        """)
        conn.commit()
        conn.close()

    def record_decision(self, decision_id: str, framework: str, problem: str, metric: str, baseline: float, target: float) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        cursor.execute("""
            INSERT OR REPLACE INTO decision_outcomes 
            (id, timestamp, framework_selected, problem_statement, target_metric_name, baseline_value, target_value, actual_value, status, arr_impact)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'IN_PROGRESS', 0.0)
        """, (decision_id, ts, framework, problem, metric, baseline, target))
        conn.commit()
        conn.close()
        return {"decision_id": decision_id, "status": "IN_PROGRESS"}

    def record_outcome(self, decision_id: str, actual_value: float, arr_impact: float) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT baseline_value, target_value FROM decision_outcomes WHERE id = ?", (decision_id,))
        row = cursor.fetchone()
        
        status = "SUCCESS"
        if row:
            target = row[1]
            if actual_value < target:
                status = "PARTIAL_SUCCESS" if actual_value > row[0] else "FAILED"
                
        cursor.execute("""
            UPDATE decision_outcomes 
            SET actual_value = ?, status = ?, arr_impact = ?
            WHERE id = ?
        """, (actual_value, status, arr_impact, decision_id))
        conn.commit()
        conn.close()
        return {"decision_id": decision_id, "status": status, "actual": actual_value, "arr_impact": arr_impact}

    def get_outcome_history(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, framework_selected, problem_statement, target_metric_name, baseline_value, target_value, actual_value, status, arr_impact FROM decision_outcomes ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": r[0], "timestamp": r[1], "framework": r[2], "problem": r[3],
            "metric": r[4], "baseline": r[5], "target": r[6], "actual": r[7],
            "status": r[8], "arr_impact": r[9]
        } for r in rows]
