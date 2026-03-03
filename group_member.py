"""
Модель GroupMember — связь пользователя и группы (many-to-many).

Поля:
  id        — первичный ключ
  group_id  — FK → groups
  user_id   — FK → users
  role      — роль: 'member' | 'admin'
  joined_at — дата вступления
"""

from datetime import datetime
from db.connection import Database


class GroupMember:
    TABLE = "group_members"

    ROLE_MEMBER = "member"
    ROLE_ADMIN = "admin"

    def __init__(self, group_id: int, user_id: int,
                 role: str = "member",
                 id: int = None, joined_at: datetime = None):
        self.id = id
        self.group_id = group_id
        self.user_id = user_id
        self.role = role
        self.joined_at = joined_at or datetime.now()

    # ── CRUD ────────────────────────────────────────────────────────────────

    def save(self) -> "GroupMember":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            """INSERT IGNORE INTO group_members (group_id, user_id, role, joined_at)
               VALUES (%s, %s, %s, %s)""",
            (self.group_id, self.user_id, self.role, self.joined_at)
        )
        db.commit()
        self.id = cursor.lastrowid
        return self

    @classmethod
    def remove(cls, group_id: int, user_id: int):
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            "DELETE FROM group_members WHERE group_id=%s AND user_id=%s",
            (group_id, user_id)
        )
        db.commit()

    @classmethod
    def get_users_in_group(cls, group_id: int) -> list:
        """Возвращает список User-объектов для данной группы."""
        from models.user import User
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            """SELECT u.* FROM users u
               JOIN group_members gm ON gm.user_id = u.id
               WHERE gm.group_id = %s""",
            (group_id,)
        )
        return [User._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_groups_of_user(cls, user_id: int) -> list:
        """Возвращает список Group-объектов, в которых состоит пользователь."""
        from models.group import Group
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            """SELECT g.* FROM `groups` g
               JOIN group_members gm ON gm.group_id = g.id
               WHERE gm.user_id = %s""",
            (user_id,)
        )
        return [Group._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def is_member(cls, group_id: int, user_id: int) -> bool:
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT 1 FROM group_members WHERE group_id=%s AND user_id=%s",
            (group_id, user_id)
        )
        return cursor.fetchone() is not None

    def __repr__(self):
        return f"<GroupMember group={self.group_id} user={self.user_id} role={self.role!r}>"
