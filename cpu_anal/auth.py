# auth and user management
#
import bcrypt
from cpu_anal.db import Database
from cpu_anal.models import User

class UserManager:
    # managers user auth and authorization

    def __init__(self, db_path: str="cpu_anal.db"):
        self.db = Database(db_path)

    async def initialize(self):
        # init db and create default admin
        await self.db.init_db()

        if not await self.db.user_exists("admin"):
            await self.create_user("admin", "admin", is_admin=True,
                                  can_view_cpu=True, can_view_memory=True,
                                  can_view_processes=True, can_view_network=True,
                                  can_kill_processes=True, can_manage_users=True)

    def hash_pass(self, pwd: str) -> str:
        # hash a pwd using bcrypt
        pass_bytes = pwd.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pass_bytes, salt)
        return hashed.decode('utf-8')

    def verify_pass(self, pwd: str, pass_hash: str) -> bool:
        # verify pass against its pass
        pass_bytes = pwd.encode('utf-8')
        hash_bytes = pass_hash.encode('utf-8')
        return bcrypt.checkpw(pass_bytes, hash_bytes)

    async def create_user(self, user: str, pwd: str, is_admin: bool = False, **permissions):
        # create new user w hashed pass
        pass_hash = self.hash_pass(pwd)
        await self.db.create_user(user, pass_hash, is_admin=is_admin, **permissions)

    async def authenticate(self, user: str, pwd: str) -> User | None:
        # auth user and return user obj if successful
        user_data = await self.db.get_user(user)

        if not user_data:
            return None
        if not self.verify_pass(pwd, user_data["pass_hash"]):
            return None

        return User(
            id=user_data["id"],
            user=user_data["user"],
            pass_hash=user_data["pass_hash"],
            is_admin=bool(user_data["is_admin"]),
            can_view_cpu=bool(user_data.get("can_view_cpu", 1)),
            can_view_memory=bool(user_data.get("can_view_memory", 0)),
            can_view_processes=bool(user_data.get("can_view_processes", 1)),
            can_view_network=bool(user_data.get("can_view_network", 1)),
            can_kill_processes=bool(user_data.get("can_kill_processes", 0)),
            can_manage_users=bool(user_data.get("can_manage_users", 0))
        )
