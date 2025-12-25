from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from uuid import uuid4

def gen_id() -> str:
    """Generate a unique ID using UUID v4"""
    return str(uuid4())

class Transaction(BaseModel):
    """Represents a financial transaction with an account"""
    id: str = Field(default_factory=gen_id)
    account_id: str
    type: Literal["income", "expense"]
    amount: float
    category: str
    memo: str
    date: str  # ISO8601 format: "YYYY-MM-DDTHH:MM:SSZ"
    item: str = ""  # 항목 필드 추가 (기본값은 빈 문자열)

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Transaction amount must be positive')
        return v

    @validator('type')
    def type_must_be_valid(cls, v):
        if v not in ("income", "expense"):
            raise ValueError('Invalid transaction type')
        return v

class ValuationRecord(BaseModel):
    """자산 평가 기록 모델"""
    id: str = Field(default_factory=gen_id)
    account_id: str
    evaluated_amount: float
    evaluation_date: str  # ISO8601 format: "YYYY-MM-DDTHH:MM:SSZ"
    memo: str = ""  # 평가 사유 또는 메모
    transaction_type: Literal["buy", "sell", "valuation"] = "valuation"  # 거래 타입 추가
    
    @validator('evaluated_amount')
    def amount_cannot_be_negative(cls, v):
        if v < 0:
            raise ValueError('Evaluation amount cannot be negative')
        return v

class TradePair(BaseModel):
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

class Account(BaseModel):
    """Account information model"""
    id: str = Field(default_factory=gen_id)
    name: str
    type: Literal["현금", "투자", "소비"]
    color: str
    opening_balance: float
    status: Literal["active", "dead"] = "active"
    image_path: str = ""
    transactions: List[Transaction] = []
    valuations: List[ValuationRecord] = []
    # Fields for investment accounts
    purchase_amount: float = 0.0 # 총 매입금액
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
    def calculated_evaluated_amount(self) -> float:
        """Calculate evaluated amount based on transaction types and dates.
        For buy transactions, accumulate all buy amounts after the last sell.
        For sell/valuation transactions, use the latest transaction amount."""
        if not self.valuations:
            return 0.0
        
        # Sort valuations by date
        sorted_valuations = sorted(self.valuations, key=lambda v: v.evaluation_date)
        latest_valuation = sorted_valuations[-1]
        
        # If the latest transaction is sell or valuation, use its amount directly
        if latest_valuation.transaction_type in ["sell", "valuation"]:
            return latest_valuation.evaluated_amount
        
        # If the latest transaction is buy, accumulate all buy amounts after the last sell
        if latest_valuation.transaction_type == "buy":
            # Find the last sell transaction index
            last_sell_index = -1
            for i, valuation in enumerate(sorted_valuations):
                if valuation.transaction_type == "sell":
                    last_sell_index = i
            
            # Sum all buy transactions after the last sell
            total_amount = 0.0
            for i in range(last_sell_index + 1, len(sorted_valuations)):
                valuation = sorted_valuations[i]
                if valuation.transaction_type == "buy":
                    total_amount += valuation.evaluated_amount
            
            return total_amount
        
        return 0.0
    
    @property
    def asset_value(self) -> float:
        """Calculate total asset value for investment accounts, or balance for others."""
        if self.type == "투자":
            return self.calculated_evaluated_amount
        return self.balance()

    def balance(self) -> float:
        """Calculate current account balance including all transactions.
        Kept for compatibility with non-investment accounts.
        """
        income = sum(t.amount for t in self.transactions if t.type == "income")
        expense = sum(t.amount for t in self.transactions if t.type == "expense")
        return self.opening_balance + income - expense

    @validator('name')
    def name_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Account name cannot be empty')
        return v.strip()

    @validator('type')
    def type_must_be_valid(cls, v):
        if v not in ("현금", "투자", "소비"):
            raise ValueError('Invalid account type')
        return v

    @validator('color')
    def color_must_be_valid_hex(cls, v):
        if not v.startswith("#") or len(v) != 7:
            raise ValueError('Color must be a valid hex code')
        return v
    
    def dict(self, **kwargs):
        """Override dict() to include computed properties"""
        data = super().dict(**kwargs)
        # Add computed properties to the dictionary
        data['return_rate'] = self.return_rate
        data['asset_value'] = self.asset_value
        return data
