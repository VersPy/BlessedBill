"""
Модель User — участник приложения.

Поля:
  id           — первичный ключ
  username     — уникальный логин
  email        — уникальный email
  password     — хэш пароля (bcrypt)
  display_name — отображаемое имя
  avatar_url   — ссылка на аватар (опционально)
  created_at   — дата регистрации
"""

import hashlib
import os
from datetime import datetime
from db.connection import Database


class User:
    TABLE = "users"

    def __init__(self, username: str, email: str, display_name: str,
                 password_hash: str = None, avatar_url: str = None,
                 id: int = None, created_at: datetime = None):
        self.id = id
        self.username = username
        self.email = email
        self.display_name = display_name
        self.password_hash = password_hash
        self.avatar_url = avatar_url
        self.created_at = created_at or datetime.now()

    # ── Хэширование пароля ──────────────────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}:{hashed}"

    def check_password(self, password: str) -> bool:
        salt, hashed = self.password_hash.split(":")
        return hashed == hashlib.sha256((salt + password).encode()).hexdigest()

    # ── CRUD ────────────────────────────────────────────────────────────────

    def save(self) -> "User":
        db = Database.get_instance()
        cursor = db.get_cursor()
        if self.id is None:
            cursor.execute(
                """INSERT INTO users (username, email, display_name, password_hash, avatar_url, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (self.username, self.email, self.display_name,
                 self.password_hash, self.avatar_url, self.created_at)
            )
            db.commit()
            self.id = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE users SET username=%s, email=%s, display_name=%s,
                   avatar_url=%s WHERE id=%s""",
                (self.username, self.email, self.display_name,
                 self.avatar_url, self.id)
            )
            db.commit()
        return self

    @classmethod
    def find_by_id(cls, user_id: int) -> "User | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_by_email(cls, email: str) -> "User | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_by_username(cls, username: str) -> "User | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    def delete(self):
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (self.id,))
        db.commit()

    # ── Вспомогательные ─────────────────────────────────────────────────────

    @classmethod
    def _from_row(cls, row: dict) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            display_name=row["display_name"],
            password_hash=row["password_hash"],
            avatar_url=row.get("avatar_url"),
            created_at=row["created_at"],
        )

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r}>"
