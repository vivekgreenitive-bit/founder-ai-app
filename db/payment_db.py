import sqlite3
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

class PaymentDBManager:
    def __init__(self, db_path: str = "conversation_history.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        cursor = self.conn.cursor()
        
        # Wallets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                blockchain TEXT NOT NULL,
                usdc_balance REAL DEFAULT 0.0,
                environment TEXT DEFAULT 'testnet'
            )
        """)
        
        # Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id TEXT PRIMARY KEY,
                wallet_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USDC',
                merchant_name TEXT NOT NULL,
                category TEXT NOT NULL,
                circle_tx_id TEXT,
                status TEXT DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(wallet_id) REFERENCES wallets(id)
            )
        """)
        
        # Policies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                max_transaction_limit REAL NOT NULL,
                daily_spending_limit REAL NOT NULL,
                monthly_budget REAL NOT NULL,
                emergency_stop INTEGER DEFAULT 0,
                approved_merchants TEXT,
                approved_categories TEXT
            )
        """)
        
        # Invoices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'unpaid',
                due_date DATETIME NOT NULL,
                invoice_pdf_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Subscriptions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                service_name TEXT NOT NULL,
                monthly_cost REAL NOT NULL,
                billing_day INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                last_payment_date DATETIME
            )
        """)
        
        # Audit Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        self._seed_default_data()

    def _seed_default_data(self) -> None:
        cursor = self.conn.cursor()
        
        # Seed default wallet if not exists
        cursor.execute("SELECT COUNT(*) FROM wallets")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO wallets (id, address, blockchain, usdc_balance, environment) VALUES (?, ?, ?, ?, ?)",
                ("primary_usdc_wallet", "0x391f...7f56d9", "Ethereum (Goerli)", 1500.00, "testnet")
            )
            
        # Seed default policy if not exists
        cursor.execute("SELECT COUNT(*) FROM policies")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO policies (max_transaction_limit, daily_spending_limit, monthly_budget, emergency_stop, approved_merchants, approved_categories) VALUES (?, ?, ?, ?, ?, ?)",
                (200.0, 500.0, 2000.0, 0, json.dumps(["Gartner", "AWS", "Google Cloud", "Zoom", "Freelancer"]), json.dumps(["Research", "Infrastructure", "Subscriptions", "Services"]))
            )

        # Seed default subscriptions if empty
        cursor.execute("SELECT COUNT(*) FROM subscriptions")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO subscriptions (id, service_name, monthly_cost, billing_day, status) VALUES (?, ?, ?, ?, ?)",
                ("sub_aws", "Amazon Web Services", 79.00, 1, "active")
            )
            cursor.execute(
                "INSERT INTO subscriptions (id, service_name, monthly_cost, billing_day, status) VALUES (?, ?, ?, ?, ?)",
                ("sub_zoom", "Zoom Video Communications", 14.99, 15, "active")
            )

        # Seed default invoices if empty
        cursor.execute("SELECT COUNT(*) FROM invoices")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO invoices (id, customer_name, amount, status, due_date) VALUES (?, ?, ?, ?, ?)",
                ("inv_001", "Beta Labs LLC", 500.00, "unpaid", "2026-08-15 00:00:00")
            )
            
        self.conn.commit()

    def get_wallet(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, address, blockchain, usdc_balance, environment FROM wallets WHERE id = ?", (wallet_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "address": row[1], "blockchain": row[2], "usdc_balance": row[3], "environment": row[4]}
        return None

    def update_wallet_balance(self, wallet_id: str, new_balance: float) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE wallets SET usdc_balance = ? WHERE id = ?", (new_balance, wallet_id))
        self.conn.commit()

    def add_transaction(self, tx_id: str, wallet_id: str, amount: float, merchant: str, category: str, circle_tx_id: str, status: str = "completed") -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO payment_transactions (id, wallet_id, amount, merchant_name, category, circle_tx_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tx_id, wallet_id, amount, merchant, category, circle_tx_id, status)
        )
        self.conn.commit()

    def get_today_spent(self) -> float:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(amount) FROM payment_transactions 
            WHERE date(created_at) = date('now') AND status != 'failed'
        """)
        row = cursor.fetchone()
        return row[0] if row[0] is not None else 0.0

    def get_active_policy(self) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT max_transaction_limit, daily_spending_limit, monthly_budget, emergency_stop, approved_merchants, approved_categories 
            FROM policies ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {
                "max_transaction_limit": row[0],
                "daily_spending_limit": row[1],
                "monthly_budget": row[2],
                "emergency_stop": row[3],
                "approved_merchants": json.loads(row[4] or "[]"),
                "approved_categories": json.loads(row[5] or "[]")
            }
        return None

    def update_policy(self, max_limit: float, daily_limit: float, monthly_budget: float, emergency_stop: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO policies (max_transaction_limit, daily_spending_limit, monthly_budget, emergency_stop, approved_merchants, approved_categories)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (max_limit, daily_limit, monthly_budget, emergency_stop, json.dumps(["Gartner", "AWS", "Google Cloud", "Zoom", "Freelancer"]), json.dumps(["Research", "Infrastructure", "Subscriptions", "Services"])))
        self.conn.commit()

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, amount, merchant_name, category, status, created_at, circle_tx_id FROM payment_transactions ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [{"id": r[0], "amount": r[1], "merchant": r[2], "category": r[3], "status": r[4], "created_at": r[5], "circle_tx_id": r[6]} for r in rows]

    def get_all_invoices(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, customer_name, amount, status, due_date FROM invoices ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [{"id": r[0], "customer": r[1], "amount": r[2], "status": r[3], "due_date": r[4]} for r in rows]

    def add_invoice(self, id: str, customer: str, amount: float, due_date: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO invoices (id, customer_name, amount, due_date) VALUES (?, ?, ?, ?)", (id, customer, amount, due_date))
        self.conn.commit()

    def get_all_subscriptions(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, service_name, monthly_cost, billing_day, status FROM subscriptions")
        rows = cursor.fetchall()
        return [{"id": r[0], "service": r[1], "cost": r[2], "billing_day": r[3], "status": r[4]} for r in rows]

    def add_subscription(self, id: str, service: str, cost: float, billing_day: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO subscriptions (id, service_name, monthly_cost, billing_day) VALUES (?, ?, ?, ?)", (id, service, cost, billing_day))
        self.conn.commit()

    def get_all_audit_logs(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, event_type, message, timestamp FROM audit_logs ORDER BY id DESC")
        rows = cursor.fetchall()
        return [{"id": r[0], "event_type": r[1], "message": r[2], "timestamp": r[3]} for r in rows]

    def add_audit_log(self, event_type: str, message: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO audit_logs (event_type, message) VALUES (?, ?)", (event_type, message))
        self.conn.commit()
