from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Literal
from datetime import datetime
import uuid

def gen_id() -> str:
    """Generate a unique ID using UUID v4"""
    return str(uuid.uuid4())

@dataclass
class Transaction:
    """Represents a financial transaction with an account"""
    id: str
    account_id: str
    type: Literal["income", "expense"]
    amount: float
    category: str
    memo: str
    date: str  # ISO8601 format: "YYYY-MM-DDTHH:MM:SSZ"
    item: str = ""  # 항목 필드 추가 (기본값은 빈 문자열)

    def validate(self) -> None:
        """Validate transaction data"""
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        if self.type not in ("income", "expense"):
            raise ValueError("Invalid transaction type")
        try:
            datetime.fromisoformat(self.date.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid date format, must be ISO8601")

@dataclass
class Account:
    """Account information model"""
    id: str
    name: str
    type: Literal["현금", "투자", "소비"]
    color: str
    opening_balance: float
    status: Literal["active", "dead"] = "active"
    image_path: str = ""
    transactions: list[Transaction] = field(default_factory=list)
    # Fields for investment accounts
    purchase_amount: float = 0.0 # 총 매입금액
    cash_holding: float = 0.0 # 보유 현금
    evaluated_amount: float = 0.0 # 현재 평가금액
    last_valuation_date: str = "" # 마지막 평가 날짜 (YYYY-MM-DD)


    @property
    def return_rate(self) -> float:
        """Calculate return rate for investment accounts."""
        if self.type == "투자" and self.purchase_amount != 0:
            return ((self.evaluated_amount - self.purchase_amount) / self.purchase_amount) * 100
        return 0.0

    @property
    def asset_value(self) -> float:
        """Calculate total asset value for investment accounts, or balance for others."""
        if self.type == "투자":
            return self.evaluated_amount + self.cash_holding
        return self.balance()

    def balance(self) -> float:
        """Calculate current account balance including all transactions.
        Kept for compatibility with non-investment accounts.
        """
        income = sum(t.amount for t in self.transactions if t.type == "income")
        expense = sum(t.amount for t in self.transactions if t.type == "expense")
        return self.opening_balance + income - expense

    def validate(self) -> None:
        """Validate account data"""
        if not self.name.strip():
            raise ValueError("Account name cannot be empty")
        if self.type not in ("현금", "투자"):
            raise ValueError("Invalid account type")
        if not self.color.startswith("#") or len(self.color) != 7:
            raise ValueError("Color must be a valid hex code")
        for txn in self.transactions:
            txn.validate()
