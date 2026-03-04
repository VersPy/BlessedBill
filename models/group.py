"""
Модель Group — группа людей, которые делят счета.

Поля:
  id          — первичный ключ
  name        — название группы (напр. "Путешествие в Берлин")
  description — описание (опционально)
  owner_id    — создатель группы (FK → users)
  created_at  — дата создания

Связанные модели:
  GroupMember — участники группы (many-to-many с User)
  Bill        — счета внутри группы
"""

from datetime import datetime
from db.connection import Database


class Group:
    TABLE = "groups"

    def __init__(self, name: str, owner_id: int,
                 description: str = None,
                 id: int = None, created_at: datetime = None):
        self.id = id
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.created_at = created_at or datetime.now()

    # ── CRUD ────────────────────────────────────────────────────────────────

    def save(self) -> "Group":
        db = Database.get_instance()
        cursor = db.get_cursor()
        if self.id is None:
            cursor.execute(
                """INSERT INTO `groups` (name, description, owner_id, created_at)
                   VALUES (%s, %s, %s, %s)""",
                (self.name, self.description, self.owner_id, self.created_at)
            )
            db.commit()
            self.id = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE `groups` SET name=%s, description=%s WHERE id=%s""",
                (self.name, self.description, self.id)
            )
            db.commit()
        return self

    @classmethod
    def find_by_id(cls, group_id: int) -> "Group | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM `groups` WHERE id = %s", (group_id,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_by_owner(cls, owner_id: int) -> list["Group"]:
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM `groups` WHERE owner_id = %s", (owner_id,))
        return [cls._from_row(row) for row in cursor.fetchall()]

    def get_members(self) -> list:
        """Возвращает список User — участников группы."""
        from models.group_member import GroupMember
        return GroupMember.get_users_in_group(self.id)

    def add_member(self, user_id: int):
        from models.group_member import GroupMember
        GroupMember(group_id=self.id, user_id=user_id).save()

    def remove_member(self, user_id: int):
        from models.group_member import GroupMember
        GroupMember.remove(group_id=self.id, user_id=user_id)

    def delete(self):
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("DELETE FROM `groups` WHERE id = %s", (self.id,))
        db.commit()

    # ── Вспомогательные ─────────────────────────────────────────────────────

    @classmethod
    def _from_row(cls, row: dict) -> "Group":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            owner_id=row["owner_id"],
            created_at=row["created_at"],
        )

    def __repr__(self):
        return f"<Group id={self.id} name={self.name!r} owner_id={self.owner_id}>"
