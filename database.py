import aiosqlite
import datetime
from config import DATABASE_NAME
from models.user import User, UserRole

class Database:
    def __init__(self):
        self.db_name = DATABASE_NAME

    async def create_tables(self):
        async with aiosqlite.connect(self.db_name) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Таблица анонимных постов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS anonymous_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    post_text TEXT NOT NULL,
                    status TEXT DEFAULT 'published',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            await db.commit()

    async def add_user(self, user_id: int, username: str, first_name: str):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM users WHERE id = ?', (user_id,)) as cursor:
                existing_user = await cursor.fetchone()
                
            if not existing_user:
                await db.execute(
                    'INSERT INTO users (id, username, first_name, role, created_at) VALUES (?, ?, ?, ?, ?)',
                    (user_id, username, first_name, UserRole.USER.value, datetime.datetime.now().isoformat())
                )
                await db.commit()

    async def get_user(self, user_id: int) -> User:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM users WHERE id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row[0],
                        username=row[1],
                        first_name=row[2],
                        role=UserRole(row[3]),
                        created_at=row[4]
                    )
                return None

    async def create_anonymous_post(self, user_id: int, post_text: str):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                'INSERT INTO anonymous_posts (user_id, post_text, created_at) VALUES (?, ?, ?)',
                (user_id, post_text, datetime.datetime.now().isoformat())
            )
            await db.commit()
            return cursor.lastrowid

    async def get_all_users(self):
        """Получить всех пользователей для рассылки"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT id FROM users') as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_users_count(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_posts_count(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT COUNT(*) FROM anonymous_posts') as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

# Глобальный экземпляр базы данных
db = Database()