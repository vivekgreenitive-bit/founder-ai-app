import sqlite3
from typing import Any

class MemoryAgent:
    db_path: str
    conn: sqlite3.Connection

    def __init__(self, db_path: str = "conversation_history.db") -> None:
        self.db_path = db_path
        # Allow multi-threaded PyQt accesses with check_same_thread=False
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the persistent SQLite database table for conversation history."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            print(f"Error initializing SQLite memory db: {e}")

    def add_record(self, query: str, framework: str, response: str) -> None:
        """Adds a strategy run record to the persistent SQLite database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO history (query, framework, response) VALUES (?, ?, ?)",
                (query, framework, response)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error adding SQLite record: {e}")

    def get_context(self) -> str:
        """Retrieves the last 3 persistent records formatted as chronological memory context."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT query, framework FROM history ORDER BY id DESC LIMIT 3")
            rows = cursor.fetchall()
            
            if not rows:
                return "No previous query history in this session."
            
            context = "Previous Session History:\n"
            for idx, (q, fw) in enumerate(reversed(rows)):
                context += f"- Run {idx+1}: Solved '{q}' using {fw}\n"
            return context
        except Exception as e:
            print(f"Error retrieving SQLite records: {e}")
            return "No previous query history in this session."

    def __del__(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
