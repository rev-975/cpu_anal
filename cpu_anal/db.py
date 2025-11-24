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
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    can_view_cpu INTEGER NOT NULL DEFAULT 1,
                    can_view_memory INTEGER NOT NULL DEFAULT 0,
                    can_view_processes INTEGER NOT NULL DEFAULT 1,
                    can_view_network INTEGER NOT NULL DEFAULT 1,
                    can_kill_processes INTEGER NOT NULL DEFAULT 0,
                    can_manage_users INTEGER NOT NULL DEFAULT 0
                )
            """)
            await db.commit()

            # Migrate existing users to have new columns
            await self._migrate_permissions(db)

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

    async def create_user(self, user: str, pass_hash: str, is_admin: bool = False,
                         can_view_cpu: bool = True, can_view_memory: bool = False,
                         can_view_processes: bool = True, can_view_network: bool = True,
                         can_kill_processes: bool = False, can_manage_users: bool = False):
        # create user
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO users (user, pass_hash, is_admin, can_view_cpu, can_view_memory,
                   can_view_processes, can_view_network, can_kill_processes, can_manage_users)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user, pass_hash, 1 if is_admin else 0,
                 1 if can_view_cpu else 0, 1 if can_view_memory else 0,
                 1 if can_view_processes else 0, 1 if can_view_network else 0,
                 1 if can_kill_processes else 0, 1 if can_manage_users else 0)
            )
            await db.commit()

    async def user_exists(self, user: str) -> bool:
        # check if user exists
        user = await self.get_user(user)
        return user is not None

    async def update_password(self, user: str, new_pass_hash: str):
        # update user password
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET pass_hash = ? WHERE user = ?",
                (new_pass_hash, user)
            )
            await db.commit()

    async def update_user_permissions(self, user: str, **permissions):
        # update user permissions
        async with aiosqlite.connect(self.db_path) as db:
            # Build dynamic SQL for only provided permissions
            updates = []
            values = []
            for key, value in permissions.items():
                if key in ['can_view_cpu', 'can_view_memory', 'can_view_processes',
                          'can_view_network', 'can_kill_processes', 'can_manage_users', 'is_admin']:
                    updates.append(f"{key} = ?")
                    values.append(1 if value else 0)

            if updates:
                values.append(user)
                sql = f"UPDATE users SET {', '.join(updates)} WHERE user = ?"
                await db.execute(sql, tuple(values))
                await db.commit()

    async def get_all_users(self) -> list[dict]:
        # get all users for management
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users ORDER BY user") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def _migrate_permissions(self, db):
        # migrate existing users to have permission columns
        try:
            # Check if columns exist by trying to select them
            await db.execute("SELECT can_view_cpu FROM users LIMIT 1")
        except Exception:
            # Columns don't exist, need to add them
            try:
                await db.execute("ALTER TABLE users ADD COLUMN can_view_cpu INTEGER NOT NULL DEFAULT 1")
                await db.execute("ALTER TABLE users ADD COLUMN can_view_memory INTEGER NOT NULL DEFAULT 0")
                await db.execute("ALTER TABLE users ADD COLUMN can_view_processes INTEGER NOT NULL DEFAULT 1")
                await db.execute("ALTER TABLE users ADD COLUMN can_view_network INTEGER NOT NULL DEFAULT 1")
                await db.execute("ALTER TABLE users ADD COLUMN can_kill_processes INTEGER NOT NULL DEFAULT 0")
                await db.execute("ALTER TABLE users ADD COLUMN can_manage_users INTEGER NOT NULL DEFAULT 0")

                # Give admins full permissions
                await db.execute("""
                    UPDATE users SET
                        can_view_cpu = 1,
                        can_view_memory = 1,
                        can_view_processes = 1,
                        can_view_network = 1,
                        can_kill_processes = 1,
                        can_manage_users = 1
                    WHERE is_admin = 1
                """)
                await db.commit()
            except Exception:
                # Columns might already exist from previous migration attempt
                pass
