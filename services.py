from __future__ import annotations
import json
from typing import Protocol, Literal, Optional
from dataclasses import asdict
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

from domain import Account, Transaction, ValuationRecord, TradePair
from PySide6.QtWidgets import QMessageBox

# ==== HELPER FUNCTIONS =====================================================

def gen_id() -> str:
    """Generate a unique ID using UUID v4"""
    import uuid
    return str(uuid.uuid4())

def today_iso() -> str:
    """Get current date/time in ISO format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    return f"₩{amount:,.0f}"

# ==== DATA LAYER ============================================================

class LedgerDataSource(Protocol):
    """Protocol for ledger data sources"""
    def load(self) -> dict: ...
    def save(self, data: dict) -> None: ...

class LocalJSONDataSource:
    """Local JSON file data source implementation"""
    
    def __init__(self, filepath: str = "ledger.json"):
        """Initialize with path to JSON file"""
        self.filepath = Path(filepath)

    def load(self) -> dict:
        """Load data from JSON file"""
        if not self.filepath.exists():
            return {"accounts": [], "salaries": []}
        try:
            return json.loads(self.filepath.read_text(encoding="utf-8"))
        except Exception as e:
            QMessageBox.warning(None, "Data Load Error", f"Failed to load data: {str(e)}")
            return {"accounts": [], "salaries": []}

    def save(self, data: dict) -> None:
        """Save data to JSON file"""
        try:
            self.filepath.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), 
                encoding="utf-8"
            )
        except Exception as e:
            QMessageBox.critical(None, "Save Error", f"Failed to save data: {str(e)}")

class RESTDataSource:
    """Stub for future REST API data source"""
    
    def __init__(self, base_url: str):
        """Initialize with base API URL"""
        self.base_url = base_url

    def load(self) -> dict:
        """Load data from REST API"""
        raise NotImplementedError("REST API integration required")

    def save(self, data: dict) -> None:
        """Save data via REST API"""
        raise NotImplementedError("REST API integration required")

# ==== REPOSITORY LAYER =====================================================

class LedgerRepository:
    """Repository for managing account and transaction persistence"""
    
    def __init__(self, data_source: LedgerDataSource):
        """Initialize with data source"""
        self.ds = data_source
        raw = self.ds.load()
        self.accounts: dict[str, Account] = {}
        self.salaries: list[dict] = []
        self._deserialize(raw)

    def _serialize(self) -> dict:
        """Serialize accounts and salaries to dict"""
        return {
            "accounts": [asdict(acc) for acc in self.accounts.values()],
            "salaries": self.salaries
        }

    def _deserialize(self, raw: dict) -> None:
        """Deserialize accounts and salaries from dict"""
        self.accounts.clear()
        self.salaries = raw.get("salaries", [])
        
        for acc_dict in raw.get("accounts", []):
            txns = [Transaction(**t) for t in acc_dict.get("transactions", [])]
            
            # 기존 평가 기록에 transaction_type 추가 (호환성 유지)
            valuations = []
            for v in acc_dict.get("valuations", []):
                # ValuationRecord 객체 생성
                valuation = ValuationRecord(**v)
                
                # transaction_type이 없는 경우 자동으로 설정
                if not hasattr(valuation, 'transaction_type') or valuation.transaction_type is None:
                    # 부동산 계좌인 경우 특별 처리
                    if acc_dict.get("name") == "부동산":
                        # 첫 번째 평가 기록은 매수, 두 번째는 매도로 설정
                        if len(valuations) == 0:
                            valuation.transaction_type = "buy"
                        else:
                            valuation.transaction_type = "sell"
                    else:
                        # 다른 투자 계좌는 기본적으로 valuation으로 설정
                        valuation.transaction_type = "valuation"
                
                valuations.append(valuation)
            
            acc = Account(
                id=acc_dict["id"],
                name=acc_dict["name"],
                type=acc_dict.get("type", "현금"),
                status=acc_dict.get("status", "active"),
                color=acc_dict["color"],
                opening_balance=acc_dict["opening_balance"],
                image_path=acc_dict.get("image_path", ""), # Load image_path, default to empty string
                purchase_amount=acc_dict.get("purchase_amount", 0.0), # Load new field
                cash_holding=acc_dict.get("cash_holding", 0.0),     # Load new field
                evaluated_amount=acc_dict.get("evaluated_amount", 0.0), # Load new field
                last_valuation_date=acc_dict.get("last_valuation_date", ""), # Load new field
                transactions=txns,
                valuations=valuations
            )
            self.accounts[acc.id] = acc

    def save(self) -> None:
        """Persist current state to data source"""
        self.ds.save(self._serialize())

    def add_account(self, account: Account) -> None:
        """Add new account to repository"""
        self.accounts[account.id] = account
        self.save()

    def update_account(self, account: Account) -> None:
        """Update existing account"""
        self.accounts[account.id] = account
        self.save()

    def delete_account(self, account_id: str) -> None:
        """Delete account by ID"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            self.save()

    def get_all_accounts(self) -> list[Account]:
        """Get all accounts"""
        return list(self.accounts.values())

    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        return self.accounts.get(account_id)

    def add_transaction(self, account_id: str, txn: Transaction) -> None:
        """Add transaction to account"""
        if account_id in self.accounts:
            self.accounts[account_id].transactions.append(txn)
            self.save()

    def add_salary(self, amount: float, month: str, person: str) -> None:
        """Add salary data"""
        self.salaries.append({"amount": amount, "month": month, "person": person})
        self.save()

    def get_salaries(self) -> list[dict]:
        """Get all salary data"""
        return self.salaries.copy()

# ==== SERVICE LAYER ========================================================

class LedgerService:
    """Core service for managing accounts and transactions"""
    
    def __init__(self, repository: LedgerRepository):
        """Initialize the ledger service with a repository"""
        self.repo = repository
        
    def add_account(self, name: str, type_: Literal["현금", "투자", "소비"], 
                   color: str, opening_balance: float, image_path: str = "") -> Account:
        """Add a new account"""
        if not name.strip():
            raise ValueError("계좌명을 입력하세요.")
        
        account = Account(
            id=gen_id(),
            name=name,
            type=type_,
            color=color,
            opening_balance=opening_balance,
            status="active",
            image_path=image_path
        )
        self.repo.add_account(account)
        return account

    def update_account(self, account: Account) -> None:
        """Update an existing account"""
        self.repo.update_account(account)

    def delete_account(self, account_id: str) -> None:
        """Delete an account"""
        self.repo.delete_account(account_id)

    def toggle_account_status(self, account_id: str) -> None:
        """Toggle account status between active and dead"""
        account = self.repo.get_account(account_id)
        if account:
            account.status = "dead" if account.status == "active" else "active"
            self.repo.update_account(account)

    def list_accounts(self) -> list[Account]:
        """Get all accounts"""
        return self.repo.get_all_accounts()

    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        return self.repo.get_account(account_id)

    def add_transaction(self, account_id: str, type_: Literal["income", "expense"],
                       amount: float, category: str, memo: str, date: str) -> Transaction:
        """Add a new transaction"""
        if amount < 0:
            raise ValueError("금액은 양수 값이어야 합니다.")
        if type_ not in ("income", "expense"):
            raise ValueError("거래 타입이 잘못되었습니다.")
        
        txn = Transaction(
            id=gen_id(), 
            account_id=account_id, 
            type=type_,
            amount=amount, 
            category=category, 
            memo=memo, 
            date=date
        )
        self.repo.add_transaction(account_id, txn)
        return txn

    def list_transactions(self, account_id: str, ascending: bool = False) -> list[Transaction]:
        """Get transactions for an account, sorted by date"""
        account = self.repo.get_account(account_id)
        if not account:
            return []
        return sorted(account.transactions, key=lambda t: t.date, reverse=not ascending)

    def month_summary(self, account_id: str, year_month: str) -> dict[str, float]:
        """Get income/expense summary for a specific month"""
        txns = self.list_transactions(account_id)
        income = sum(t.amount for t in txns if t.type == "income" and t.date.startswith(year_month))
        expense = sum(t.amount for t in txns if t.type == "expense" and t.date.startswith(year_month))
        return {"income": income, "expense": expense}

    def total_assets(self) -> float:
        """Calculate total assets (excluding consumption accounts)"""
        total = 0.0
        for acc in self.list_accounts():
            if acc.type == "소비":
                continue
            if acc.type == "투자":
                total += acc.asset_value
            else: # For "현금" and any other future types
                total += acc.balance()
        return total

    def total_cash(self) -> float:
        """Calculate total cash balance"""
        return sum(acc.balance() for acc in self.list_accounts() if acc.type == "현금")

    def add_salary(self, amount: float, month: str, person: str) -> None:
        """Add salary data"""
        if amount <= 0:
            raise ValueError("월급은 0보다 커야 합니다.")
        self.repo.add_salary(amount, month, person)

    def get_salaries(self, year: Optional[str] = None) -> list[dict]:
        """Get all salary data, optionally filtered by year"""
        all_salaries = self.repo.get_salaries()
        if year:
            return [s for s in all_salaries if s["month"].startswith(year)]
        return all_salaries

    def monthly_income_breakdown(self, year: Optional[str] = None) -> dict[str, dict]:
        """Returns monthly income breakdown (savings, interest, expense), optionally filtered by year."""
        monthly_data = defaultdict(lambda: {"savings": 0, "interest": 0, "expense": 0})
        
        for account in self.list_accounts():
            if account.type != "현금":
                continue
            for txn in account.transactions:
                year_month = txn.date[:7]  # YYYY-MM
                if year and not year_month.startswith(year):
                    continue
                if txn.type == "income":
                    if txn.category == "저축":
                        monthly_data[year_month]["savings"] += txn.amount
                    elif txn.category == "이자":
                        monthly_data[year_month]["interest"] += txn.amount
                elif txn.type == "expense" and txn.category == "지출":
                    monthly_data[year_month]["expense"] += txn.amount
        
        return dict(sorted(monthly_data.items()))

    def add_valuation(self, account_id: str, amount: float, date: str, memo: str = "", transaction_type: Literal["buy", "sell", "valuation"] = "valuation") -> ValuationRecord:
        """투자 계좌에 새로운 평가 기록 추가"""
        account = self.get_account(account_id)
        if not account:
            raise ValueError("Account not found")
        if account.type != "투자":
            raise ValueError("Valuation is only available for investment accounts")
        
        valuation = ValuationRecord(
            id=gen_id(),
            account_id=account_id,
            evaluated_amount=amount,
            evaluation_date=date,
            memo=memo,
            transaction_type=transaction_type
        )
        account.valuations.append(valuation)
        
        # 호환성을 위해 기존 필드도 업데이트
        account.evaluated_amount = amount
        account.last_valuation_date = date[:10]  # YYYY-MM-DD 형식으로 저장
        
        self.repo.update_account(account)
        return valuation
    
    def get_valuations(self, account_id: str) -> list[ValuationRecord]:
        """계좌의 모든 평가 기록 반환 (날짜순 정렬)"""
        account = self.get_account(account_id)
        if not account:
            return []
        return sorted(account.valuations, key=lambda v: v.evaluation_date)
    
    def delete_valuation(self, account_id: str, valuation_id: str) -> None:
        """특정 평가 기록 삭제"""
        account = self.get_account(account_id)
        if not account:
            raise ValueError("Account not found")
        
        account.valuations = [v for v in account.valuations if v.id != valuation_id]
        # 삭제 후 최신 평가 기록으로 호환성 필드 업데이트
        if account.valuations:
            latest = account.latest_valuation
            account.evaluated_amount = latest.evaluated_amount
            account.last_valuation_date = latest.evaluation_date[:10]
        else:
            account.evaluated_amount = 0.0
            account.last_valuation_date = ""
        
        self.repo.update_account(account)
    
    def get_valuation_history(self, account_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[ValuationRecord]:
        """특정 기간의 평가 기록 반환"""
        valuations = self.get_valuations(account_id)
        
        if start_date:
            valuations = [v for v in valuations if v.evaluation_date >= start_date]
        if end_date:
            valuations = [v for v in valuations if v.evaluation_date <= end_date]
            
        return valuations
    
    def get_trade_pairs(self, account_id: str) -> list[TradePair]:
        """계좌의 매수/매도 쌍 반환 - 단순화된 동적 페어링 로직"""
        valuations = self.get_valuations(account_id)
        
        pairs = []
        unpaired_buys = []  # 페어링되지 않은 buy 기록들
        
        for valuation in valuations:
            if valuation.transaction_type == "buy":
                # buy 기록은 일단 unpaired 목록에 추가
                unpaired_buys.append(valuation)
                
            elif valuation.transaction_type == "sell":
                # sell 기록이면 가장 오래된 unpaired buy와 페어링
                if unpaired_buys:
                    buy_val = unpaired_buys.pop(0)  # 가장 오래된 buy
                    pair = TradePair(buy_valuation=buy_val, sell_valuation=valuation)
                    pairs.append(pair)
                    
            elif valuation.transaction_type == "valuation":
                # valuation 기록이면 가장 오래된 unpaired buy와 페어링
                if unpaired_buys:
                    # 이 buy가 이미 다른 valuation과 페어링되었는지 확인
                    buy_val = unpaired_buys[0]
                    
                    # 이미 pairs에 이 buy가 포함된 pair가 있는지 확인
                    existing_pair_with_buy = None
                    for pair in pairs:
                        if pair.buy_valuation.id == buy_val.id:
                            existing_pair_with_buy = pair
                            break
                    
                    if existing_pair_with_buy:
                        # 기존에 valuation과 페어링된 pair가 있으면 제거
                        pairs.remove(existing_pair_with_buy)
                    
                    # 새로운 valuation과 페어링
                    pair = TradePair(buy_valuation=buy_val, sell_valuation=valuation)
                    pairs.append(pair)
        
        return pairs
