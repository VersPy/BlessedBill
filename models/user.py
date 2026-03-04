"""
Модель User — участник Telegram Mini App.

Поля:
  id           — внутренний первичный ключ
  tg_id        — Telegram user_id (уникальный, основной идентификатор)
  tg_username  — @username в Telegram (опционально, не у всех есть)
  display_name — имя пользователя (first_name из Telegram)
  avatar_url   — ссылка на аватар (опционально)
  created_at   — дата первого входа

Авторизация:
  Telegram Mini App передаёт initData с подписанными данными пользователя.
  Пароли не нужны — идентификация идёт по tg_id.
"""

from datetime import datetime
from db.connection import Database


class User:
    TABLE = "users"

    def __init__(self, tg_id: int, display_name: str,
                 tg_username: str = None,
                 avatar_url: str = None,
                 id: int = None,
                 created_at: datetime = None):
        self.id = id
        self.tg_id = tg_id
        self.tg_username = tg_username
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.created_at = created_at or datetime.now()

    # ── CRUD ────────────────────────────────────────────────────────────────

    def save(self) -> "User":
        db = Database.get_instance()
        cursor = db.get_cursor()
        if self.id is None:
            cursor.execute(
                """INSERT INTO users (tg_id, tg_username, display_name, avatar_url, created_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (self.tg_id, self.tg_username, self.display_name,
                 self.avatar_url, self.created_at)
            )
            db.commit()
            self.id = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE users SET tg_username=%s, display_name=%s, avatar_url=%s
                   WHERE id=%s""",
                (self.tg_username, self.display_name, self.avatar_url, self.id)
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
    def find_by_tg_id(cls, tg_id: int) -> "User | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM users WHERE tg_id = %s", (tg_id,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_by_tg_username(cls, tg_username: str) -> "User | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM users WHERE tg_username = %s", (tg_username,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def get_or_create_from_tg(cls, tg_id: int, display_name: str,
                               tg_username: str = None,
                               avatar_url: str = None) -> tuple["User", bool]:
        """
        Найти пользователя по tg_id или создать нового.
        Возвращает (user, created: bool).
        Вызывается при каждом открытии Mini App.
        """
        user = cls.find_by_tg_id(tg_id)
        if user:
            # Обновить данные если изменились
            user.display_name = display_name
            user.tg_username = tg_username
            user.avatar_url = avatar_url
            user.save()
            return user, False
        user = cls(
            tg_id=tg_id,
            display_name=display_name,
            tg_username=tg_username,
            avatar_url=avatar_url,
        )
        user.save()
        return user, True

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
            tg_id=row["tg_id"],
            tg_username=row.get("tg_username"),
            display_name=row["display_name"],
            avatar_url=row.get("avatar_url"),
            created_at=row["created_at"],
        )

    def __repr__(self):
        return f"<User id={self.id} tg_id={self.tg_id} username=@{self.tg_username}>"