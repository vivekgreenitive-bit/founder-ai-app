import unittest
from agents.memory_agent import MemoryAgent

class TestMemoryBehavior(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryAgent(db_path=":memory:")

    def test_first_interaction_empty_history(self):
        ctx = self.memory.get_context()
        self.assertEqual(ctx, "No previous query history in this session.")

    def test_follow_up_adds_context(self):
        self.memory.add_record(
            query="How do I launch BakerConnect?",
            framework="ECG KISS",
            response="Apply Bakers setup steps..."
        )
        ctx = self.memory.get_context()
        self.assertIn("Run 1: Solved 'How do I launch BakerConnect?' using ECG KISS", ctx)

    def test_context_limit_history_size(self):
        # Add 5 records. MemoryAgent should only return the last 3.
        for i in range(1, 6):
            self.memory.add_record(
                query=f"Query {i}",
                framework="ECG KISS",
                response=f"Response {i}"
            )
        ctx = self.memory.get_context()
        self.assertNotIn("Query 1", ctx)
        self.assertNotIn("Query 2", ctx)
        self.assertIn("Query 3", ctx)
        self.assertIn("Query 4", ctx)
        self.assertIn("Query 5", ctx)

    def test_topic_change(self):
        self.memory.add_record("Low sales issues", "RUN DCMS ER", "Revenue actions...")
        # Topic changes to daily planning
        ctx = self.memory.get_context()
        self.assertIn("Low sales issues", ctx)
        self.assertIn("RUN DCMS ER", ctx)

if __name__ == '__main__':
    unittest.main()
