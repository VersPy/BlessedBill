"""
Модель BillSplit — доля конкретного пользователя в счёте.

Поля:
  id         — первичный ключ
  bill_id    — FK → bills
  user_id    — FK → users
  amount     — сумма долга
  is_paid    — погашен ли долг
  paid_at    — когда погашен (опционально)
"""

from datetime import datetime
from decimal import Decimal
from db.connection import Database


class BillSplit:
    TABLE = "bill_splits"

    def __init__(self, bill_id: int, user_id: int, amount: Decimal,
                 is_paid: bool = False,
                 id: int = None,
                 paid_at: datetime = None):
        self.id = id
        self.bill_id = bill_id
        self.user_id = user_id
        self.amount = Decimal(str(amount))
        self.is_paid = is_paid
        self.paid_at = paid_at

    # ── CRUD ────────────────────────────────────────────────────────────────

    def save(self) -> "BillSplit":
        db = Database.get_instance()
        cursor = db.get_cursor()
        if self.id is None:
            cursor.execute(
                """INSERT INTO bill_splits (bill_id, user_id, amount, is_paid, paid_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (self.bill_id, self.user_id, self.amount,
                 self.is_paid, self.paid_at)
            )
            db.commit()
            self.id = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE bill_splits SET amount=%s, is_paid=%s, paid_at=%s
                   WHERE id=%s""",
                (self.amount, self.is_paid, self.paid_at, self.id)
            )
            db.commit()
        return self

    @classmethod
    def find_by_bill(cls, bill_id: int) -> list["BillSplit"]:
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT * FROM bill_splits WHERE bill_id = %s", (bill_id,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def find_by_user(cls, user_id: int) -> list["BillSplit"]:
        """Все долги пользователя (неоплаченные и оплаченные)."""
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT * FROM bill_splits WHERE user_id = %s", (user_id,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_user_debt_in_group(cls, user_id: int, group_id: int) -> Decimal:
        """Суммарный долг пользователя в группе."""
        db = Database.get_instance()
        cursor = db.get_cursor()
        cursor.execute(
            """SELECT COALESCE(SUM(bs.amount), 0) AS total
               FROM bill_splits bs
               JOIN bills b ON b.id = bs.bill_id
               WHERE bs.user_id = %s AND b.group_id = %s AND bs.is_paid = FALSE""",
            (user_id, group_id)
        )
        row = cursor.fetchone()
        return Decimal(str(row["total"]))

    # ── Бизнес-логика ───────────────────────────────────────────────────────

    def mark_paid(self):
        """Отметить долю как оплаченную."""
        self.is_paid = True
        self.paid_at = datetime.now()
        self.save()

    # ── Вспомогательные ─────────────────────────────────────────────────────

    @classmethod
    def _from_row(cls, row: dict) -> "BillSplit":
        return cls(
            id=row["id"],
            bill_id=row["bill_id"],
            user_id=row["user_id"],
            amount=row["amount"],
            is_paid=bool(row["is_paid"]),
            paid_at=row.get("paid_at"),
        )

    def __repr__(self):
        status = "✅" if self.is_paid else "❌"
        return f"<BillSplit bill={self.bill_id} user={self.user_id} amount={self.amount} {status}>"
