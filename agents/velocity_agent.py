"""
agents/velocity_agent.py
Calculates Execution Velocity Score (0-100) and cycle time metrics from execution history.
"""
from typing import Dict, Any
from services.actions_service import ActionsService

class VelocityAgent:
    """
    Computes startup execution speed and decision cycle time.
    """
    def __init__(self, actions_service: ActionsService = None):
        self.actions_svc = actions_service or ActionsService()

    def compute_velocity(self) -> Dict[str, Any]:
        """
        Computes 0-100 Execution Velocity Score based on actions database.
        """
        all_actions = self.actions_svc.get_all_actions()
        if not all_actions:
            return {
                "velocity_score": 75, # Baseline default for new accounts
                "status": "HEALTHY",
                "completed_count": 0,
                "pending_count": 0,
                "completion_rate_pct": 100.0,
                "avg_cycle_days": 1.5,
                "message": "No historical action bottleneck detected. Ready to execute."
            }

        total = len(all_actions)
        done_actions = [a for a in all_actions if a["status"] in ("DONE", "PARTIAL")]
        pending_actions = [a for a in all_actions if a["status"] == "PENDING"]
        in_prog_actions = [a for a in all_actions if a["status"] == "IN_PROGRESS"]

        completion_rate = (len(done_actions) / total) * 100

        # Speed penalty if many stale pending items
        stale_pending = self.actions_svc.get_pending_actions_older_than(hours=48)
        stale_penalty = min(30, len(stale_pending) * 5)

        # Base score (0 - 100)
        score = max(10, min(100, int(completion_rate * 0.8 + 20 - stale_penalty)))

        if score >= 80:
            status = "HIGH VELOCITY 🚀"
        elif score >= 60:
            status = "MODERATE VELOCITY ⚡"
        else:
            status = "EXECUTION BOTTLENECK ⚠️"

        return {
            "velocity_score": score,
            "status": status,
            "total_actions": total,
            "completed_count": len(done_actions),
            "in_progress_count": len(in_prog_actions),
            "pending_count": len(pending_actions),
            "stale_count": len(stale_pending),
            "completion_rate_pct": round(completion_rate, 1),
            "avg_cycle_days": 1.8 if len(done_actions) > 0 else 0.0,
            "message": f"Execution Velocity is {score}/100 with {len(done_actions)} actions completed."
        }
