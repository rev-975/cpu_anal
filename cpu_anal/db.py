# db setup and management

import aiosqlite
from pathlib import Path 

class Database:
   # sqlite db operations

    def __init__(self, db_path: str = "cpu_anal.db"):
        self.db_path = db_path

    async def init_db(self):
        # init db with req tables 
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT UNIQUE NOT NULL,
                    pass_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                )
            """)
            await db.commit()

    async def get_user(self, user: str) -> dict | None:
        # fetch user from username
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row 
            async with db.execute(
                "SELECT * FROM users WHERE user = ?", (user, )
            ) as cursor:
                row = await cursor.fetchone()
                if row: 
                    return dict(row)
                return None

    async def create_user(self, user: str, pass_hash: str, is_admin: bool = False):
        # create user 
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO users (user, pass_hash, is_admin) VALUES (?, ?, ?)",
                (user, pass_hash, 1 if is_admin else 0)
            )
            await db.commit()

    async def user_exists(self, user: str) -> bool:
        # check if user exists 
        user = await self.get_user(user)
        return user is not None
