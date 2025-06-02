import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import Config

class Database:
    def __init__(self, db_path: str = "vpnbot.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    full_name TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS configs (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    inbound_id INTEGER,
                    email TEXT,
                    uuid TEXT,
                    port INTEGER,
                    flow TEXT,
                    data TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_id ON configs(user_id);
                CREATE INDEX IF NOT EXISTS idx_config_active ON configs(is_active);
            """)

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        cursor = self.conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", 
            (telegram_id,)
        )
        return cursor.fetchone()

    def add_user(self, user_data: Dict) -> None:
        self.conn.execute(
            "INSERT INTO users (telegram_id, username, full_name, is_admin) VALUES (?, ?, ?, ?)",
            (
                user_data["id"],
                user_data.get("username"),
                user_data.get("full_name"),
                user_data["id"] in Config.ADMIN_IDS
            )
        )
        self.conn.commit()

    def create_config(self, user_id: int, config_data: Dict) -> str:
        config_id = f"cfg-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        expires_at = (datetime.now() + timedelta(days=Config.DEFAULT_EXPIRE_DAYS)) if Config.DEFAULT_EXPIRE_DAYS > 0 else None
        
        self.conn.execute(
            "INSERT INTO configs (id, user_id, inbound_id, email, uuid, port, flow, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                config_id, user_id, config_data["inbound_id"],
                config_data["email"], config_data["uuid"],
                config_data["port"], config_data["flow"],
                config_data["data"]
            )
        )
        self.conn.commit()
        return config_id

    def get_user_configs(self, user_id: int) -> List[Dict]:
        cursor = self.conn.execute(
            "SELECT id, inbound_id, email, uuid, port, flow, data FROM configs WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )
        return cursor.fetchall()

    def delete_config(self, config_id: str) -> bool:
        self.conn.execute(
            "UPDATE configs SET is_active = 0 WHERE id = ?",
            (config_id,)
        )
        self.conn.commit()
        return True

    def count_user_configs(self, user_id: int) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM configs WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )
        return cursor.fetchone()[0]

    def get_detailed_stats(self) -> List[Dict]:
        cursor = self.conn.execute("""
            SELECT 
                strftime('%Y-%m-%d', created_at) as date,
                COUNT(*) as new_users
            FROM users
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """)
        return cursor.fetchall()
