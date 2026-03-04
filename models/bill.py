"""
Модель Bill — счёт, который делится между участниками группы.

Поля:
  id           — первичный ключ
  group_id     — FK → groups
  payer_id     — кто заплатил (FK → users)
  title        — название (напр. "Ужин в ресторане")
  total_amount — общая сумма
  currency     — валюта (по умолчанию 'RUB')
  split_type   — способ разбивки: 'equal' | 'custom' | 'percentage'
  status       — статус: 'open' | 'settled'
  created_at   — дата создания
  settled_at   — дата закрытия (опционально)

Связанные модели:
  BillSplit — доля каждого участника
"""

from datetime import datetime
from decimal import Decimal
from db.connection import Database


class Bill:
    TABLE = "bills"

    SPLIT_EQUAL = "equal"
    SPLIT_CUSTOM = "custom"
    SPLIT_PERCENTAGE = "percentage"

    STATUS_OPEN = "open"
    STATUS_SETTLED = "settled"

    def __init__(self, group_id: int, payer_id: int, title: str,
                 total_amount: Decimal,
                 currency: str = "RUB",
                 split_type: str = "equal",
                 status: str = "open",
                 id: int = None,
                 created_at: datetime = None,
                 settled_at: datetime = None):
        self.id = id
        self.group_id = group_id
        self.payer_id = payer_id
        self.title = title
        self.total_amount = Decimal(str(total_amount))
        self.currency = currency
        self.split_type = split_type
        self.status = status
        self.created_at = created_at or datetime.now()
        self.settled_at = settled_at

    # ── CRUD ────────────────────────────────────────────────────────────────

    def save(self) -> "Bill":
        db = Database.get_instance()
        cursor = db.get_cursor()
        if self.id is None:
            cursor.execute(
                """INSERT INTO bills
                   (group_id, payer_id, title, total_amount, currency,
                    split_type, status, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (self.group_id, self.payer_id, self.title,
                 self.total_amount, self.currency,
                 self.split_type, self.status, self.created_at)
            )
            db.commit()
            self.id = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE bills SET title=%s, total_amount=%s, split_type=%s,
                   status=%s, settled_at=%s WHERE id=%s""",
                (self.title, self.total_amount, self.split_type,
                 self.status, self.settled_at, self.id)
            )
            db.commit()
        return self

    @classmethod
    def find_by_id(cls, bill_id: int) -> "Bill | None":
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_by_group(cls, group_id: int) -> list["Bill"]:
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT * FROM bills WHERE group_id = %s ORDER BY created_at DESC",
            (group_id,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]

    # ── Бизнес-логика ───────────────────────────────────────────────────────

    def split_equally(self, user_ids: list[int]):
        """Разбить счёт поровну между пользователями."""
        from models.bill_split import BillSplit
        if not user_ids:
            raise ValueError("Список участников не может быть пустым")
        share = round(self.total_amount / len(user_ids), 2)
        for user_id in user_ids:
            BillSplit(
                bill_id=self.id,
                user_id=user_id,
                amount=share
            ).save()
        self.split_type = self.SPLIT_EQUAL
        self.save()

    def split_custom(self, shares: dict[int, Decimal]):
        """
        Разбить счёт с произвольными суммами.
        shares = {user_id: amount, ...}
        """
        from models.bill_split import BillSplit
        total = sum(Decimal(str(v)) for v in shares.values())
        if round(total, 2) != round(self.total_amount, 2):
            raise ValueError(
                f"Сумма долей {total} не совпадает с суммой счёта {self.total_amount}"
            )
        for user_id, amount in shares.items():
            BillSplit(bill_id=self.id, user_id=user_id, amount=amount).save()
        self.split_type = self.SPLIT_CUSTOM
        self.save()

    def get_splits(self) -> list:
        """Вернуть все доли BillSplit для этого счёта."""
        from models.bill_split import BillSplit
        return BillSplit.find_by_bill(self.id)

    def settle(self):
        """Закрыть счёт."""
        self.status = self.STATUS_SETTLED
        self.settled_at = datetime.now()
        self.save()

    def delete(self):
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute("DELETE FROM bills WHERE id = %s", (self.id,))
        db.commit()

    # ── Вспомогательные ─────────────────────────────────────────────────────

    @classmethod
    def _from_row(cls, row: dict) -> "Bill":
        return cls(
            id=row["id"],
            group_id=row["group_id"],
            payer_id=row["payer_id"],
            title=row["title"],
            total_amount=row["total_amount"],
            currency=row["currency"],
            split_type=row["split_type"],
            status=row["status"],
            created_at=row["created_at"],
            settled_at=row.get("settled_at"),
        )

    def __repr__(self):
        return (f"<Bill id={self.id} title={self.title!r} "
                f"total={self.total_amount} {self.currency} status={self.status!r}>")
