from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Literal, Optional
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
class ValuationRecord:
    """자산 평가 기록 모델"""
    id: str
    account_id: str
    evaluated_amount: float
    evaluation_date: str  # ISO8601 format: "YYYY-MM-DDTHH:MM:SSZ"
    memo: str = ""  # 평가 사유 또는 메모
    transaction_type: Literal["buy", "sell", "valuation"] = "valuation"  # 거래 타입 추가
    
    def validate(self) -> None:
        """Validate valuation record data"""
        if self.evaluated_amount < 0:
            raise ValueError("Evaluation amount cannot be negative")
        try:
            datetime.fromisoformat(self.evaluation_date.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid date format, must be ISO8601")

@dataclass
class TradePair:
    """매수/매도 쌍 모델 - 반드시 매수와 매도가 한 쌍을 이루어야 함"""
    buy_valuation: ValuationRecord
    sell_valuation: ValuationRecord  # 매도는 필수
    
    @property
    def return_rate(self) -> float:
        """수익률 계산"""
        buy_amount = self.buy_valuation.evaluated_amount
        sell_amount = self.sell_valuation.evaluated_amount
        if buy_amount == 0:
            return 0.0
        return ((sell_amount - buy_amount) / buy_amount) * 100
    
    @property
    def profit_amount(self) -> float:
        """수익금액 계산"""
        return self.sell_valuation.evaluated_amount - self.buy_valuation.evaluated_amount

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
    valuations: list[ValuationRecord] = field(default_factory=list)
    # Fields for investment accounts
    purchase_amount: float = 0.0 # 총 매입금액
    cash_holding: float = 0.0 # 보유 현금
    evaluated_amount: float = 0.0 # 현재 평가금액 (호환성 유지)
    last_valuation_date: str = "" # 마지막 평가 날짜 (YYYY-MM-DD) (호환성 유지)

    @property
    def latest_valuation(self) -> Optional[ValuationRecord]:
        """가장 최신 평가 기록 반환"""
        if not self.valuations:
            return None
        return max(self.valuations, key=lambda v: v.evaluation_date)
    
    @property
    def return_rate(self) -> float:
        """Calculate return rate for investment accounts."""
        if self.type == "투자" and self.valuations:
            # 부동산 계좌인 경우: 첫 buy 거래와 마지막 sell 거래로 수익률 계산
            if "부동산" in self.name:
                buy_valuations = [v for v in self.valuations if v.transaction_type == "buy"]
                sell_valuations = [v for v in self.valuations if v.transaction_type == "sell"]
                
                if buy_valuations and sell_valuations:
                    first_buy = min(buy_valuations, key=lambda v: v.evaluation_date)
                    last_sell = max(sell_valuations, key=lambda v: v.evaluation_date)
                    
                    buy_amount = first_buy.evaluated_amount
                    sell_amount = last_sell.evaluated_amount
                    
                    if buy_amount != 0:
                        return ((sell_amount - buy_amount) / buy_amount) * 100
            
            # 다른 투자 계좌 또는 부동산 계좌이지만 buy/sell이 없는 경우: 기존 로직 사용
            elif self.purchase_amount != 0:
                current_value = self.evaluated_amount
                if self.valuations:
                    current_value = self.latest_valuation.evaluated_amount
                return ((current_value - self.purchase_amount) / self.purchase_amount) * 100
        
        return 0.0

    @property
    def asset_value(self) -> float:
        """Calculate total asset value for investment accounts, or balance for others."""
        if self.type == "투자":
            current_value = self.evaluated_amount
            if self.valuations:
                current_value = self.latest_valuation.evaluated_amount
            return current_value + self.cash_holding
        return self.balance()

    def balance(self) -> float:
        """Calculate current account balance including all transactions.
        Kept for compatibility with non-investment accounts.
        """
        income = sum(t.amount for t in self.transactions if t.type == "income")
        expense = sum(t.amount for t in self.transactions if t.type == "expense")
        return self.opening_balance + income - expense

    def add_valuation(self, amount: float, date: str, memo: str = "") -> ValuationRecord:
        """새로운 평가 기록 추가"""
        valuation = ValuationRecord(
            id=gen_id(),
            account_id=self.id,
            evaluated_amount=amount,
            evaluation_date=date,
            memo=memo
        )
        self.valuations.append(valuation)
        # 호환성을 위해 기존 필드도 업데이트
        self.evaluated_amount = amount
        self.last_valuation_date = date[:10]  # YYYY-MM-DD 형식으로 저장
        return valuation

    def validate(self) -> None:
        """Validate account data"""
        if not self.name.strip():
            raise ValueError("Account name cannot be empty")
        if self.type not in ("현금", "투자", "소비"):
            raise ValueError("Invalid account type")
        if not self.color.startswith("#") or len(self.color) != 7:
            raise ValueError("Color must be a valid hex code")
        for txn in self.transactions:
            txn.validate()
        for valuation in self.valuations:
            valuation.validate()
