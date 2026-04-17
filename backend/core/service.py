from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from collections import defaultdict
from models.domain import Account, Transaction, ValuationRecord, TradePair
from core.repository import LedgerRepository
from core.asset_allocation import ASSET_CATEGORY_KEYS, compute_asset_allocation_categories
from core.salary_uniqueness import (
    assert_unique_salary_record,
    normalize_salary_month,
    normalize_salary_person,
    parse_classification_for_write,
)

STOCK_PERSONS = ("민규", "하영")
STOCK_CATEGORIES = ("지수", "섹터 ETF", "종목")
STOCK_MARKETS = ("국장", "미장")

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
            name=name,
            type=type_,
            color=color,
            opening_balance=opening_balance,
            status="active",
            image_path=image_path
        )
        self.repo.save_account(account)
        return account

    def update_account(self, account: Account) -> None:
        """Update an existing account"""
        self.repo.save_account(account)

    def delete_account(self, account_id: str) -> None:
        """Delete an account"""
        self.repo.delete_account(account_id)

    def toggle_account_status(self, account_id: str) -> None:
        """Toggle account status between active and dead"""
        account = self.repo.get_account(account_id)
        if account:
            account.status = "dead" if account.status == "active" else "active"
            self.repo.save_account(account)

    def list_accounts(self) -> List[Account]:
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
        
        transaction = Transaction(
            account_id=account_id,
            type=type_,
            amount=amount,
            category=category,
            memo=memo,
            date=date
        )
        self.repo.add_transaction(account_id, transaction)
        return transaction

    def update_transaction(self, account_id: str, transaction_id: str, type_: Literal["income", "expense"],
                          amount: float, category: str, memo: str, date: str) -> Transaction:
        """Update an existing transaction"""
        if amount < 0:
            raise ValueError("금액은 양수 값이어야 합니다.")
        if type_ not in ("income", "expense"):
            raise ValueError("거래 타입이 잘못되었습니다.")
        
        # Helper to find existing transaction to preserve ID and other fields if needed
        account = self.repo.get_account(account_id)
        if not account:
            raise ValueError("계좌를 찾을 수 없습니다.")
        
        existing_transaction = None
        for t in account.transactions:
            if t.id == transaction_id:
                existing_transaction = t
                break
        
        if not existing_transaction:
            raise ValueError("거래 내역을 찾을 수 없습니다.")

        updated_transaction = Transaction(
            id=transaction_id,
            account_id=account_id,
            type=type_,
            amount=amount,
            category=category,
            memo=memo,
            date=date
        )
        self.repo.update_transaction(account_id, updated_transaction)
        return updated_transaction

    def delete_transaction(self, account_id: str, transaction_id: str) -> None:
        """Delete a transaction"""
        account = self.repo.get_account(account_id)
        if not account:
            raise ValueError("계좌를 찾을 수 없습니다.")
        
        # Remove the transaction from the account's transactions list
        account.transactions = [t for t in account.transactions if t.id != transaction_id]
        self.repo.save_account(account)

    def list_transactions(self, account_id: str, ascending: bool = False) -> List[Transaction]:
        """Get transactions for an account, sorted by date"""
        account = self.repo.get_account(account_id)
        if not account:
            return []
        return sorted(account.transactions, key=lambda t: t.date, reverse=not ascending)

    def month_summary(self, account_id: str, year_month: str) -> Dict[str, float]:
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

    def add_salary(self, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Add salary data"""
        if amount <= 0:
            raise ValueError("월급은 0보다 커야 합니다.")
        month_n = normalize_salary_month(month)
        person_n = normalize_salary_person(person)
        cls_key = parse_classification_for_write(classification)
        assert_unique_salary_record(self.repo.get_salaries(), month_n, person_n, cls_key, skip_index=None)
        stored: Optional[str] = "보너스" if cls_key == "보너스" else None
        self.repo.add_salary(amount, month_n, person_n, stored)

    def update_salary(self, index: int, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Update salary data by index"""
        if amount <= 0:
            raise ValueError("월급은 0보다 커야 합니다.")
        salaries = self.repo.get_salaries()
        if index < 0 or index >= len(salaries):
            raise ValueError("존재하지 않는 월급 항목입니다.")
        month_n = normalize_salary_month(month)
        person_n = normalize_salary_person(person)
        cls_key = parse_classification_for_write(classification)
        assert_unique_salary_record(salaries, month_n, person_n, cls_key, skip_index=index)
        stored: Optional[str] = "보너스" if cls_key == "보너스" else None
        self.repo.update_salary(index, amount, month_n, person_n, stored)
    
    def delete_salary(self, index: int) -> None:
        """Delete salary data by index"""
        self.repo.delete_salary(index)

    def get_salaries(self, year: Optional[str] = None, person: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all salary data, optionally filtered by year and person"""
        all_salaries = self.repo.get_salaries()
        if year:
            all_salaries = [s for s in all_salaries if s["month"].startswith(year)]
        if person:
            all_salaries = [s for s in all_salaries if s["person"] == person]
        return all_salaries

    def get_monthly_salary_totals(self, year: Optional[str] = None, person: Optional[str] = None) -> Dict[str, float]:
        """Calculate total salary for each month, optionally filtered by year and person.
        This aggregates all salary-related entries (e.g., 월급, 보너스) for each month.
        """
        monthly_totals = defaultdict(float)
        salaries = self.get_salaries(year=year, person=person)
        for s in salaries:
            month_key = s["month"]  # Expecting YYYY-MM format
            monthly_totals[month_key] += s["amount"]
        return dict(sorted(monthly_totals.items()))

    def calculate_salary_median(self, year: Optional[str] = None, person: Optional[str] = None) -> Optional[float]:
        """Calculate the median of monthly salary totals, optionally filtered by year and person.
        If 1월에 월급이랑 보너스를 둘 다 받았다면 그 둘을 더해 1월 총액을 삼고,
        이를 기준으로 월들의 중앙값을 찾습니다.
        """
        monthly_totals = self.get_monthly_salary_totals(year=year, person=person)
        if not monthly_totals:
            return None

        # Extract only the aggregated amounts and sort them
        amounts = sorted(list(monthly_totals.values()))
        n = len(amounts)

        if n % 2 == 1:  # Odd number of months
            return amounts[n // 2]
        else:  # Even number of months
            return amounts[n // 2 -1]

    def monthly_income_breakdown(self, year: Optional[str] = None) -> Dict[str, Dict]:
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
            account_id=account_id,
            evaluated_amount=amount,
            evaluation_date=date,
            memo=memo,
            transaction_type=transaction_type
        )
        self.repo.add_valuation(account_id, valuation)
        return valuation
    
    def get_valuations(self, account_id: str) -> List[ValuationRecord]:
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
        account.evaluated_amount = account.calculated_evaluated_amount
        if account.valuations:
            latest = account.latest_valuation
            account.last_valuation_date = latest.evaluation_date[:10]
        else:
            account.last_valuation_date = ""
        
        self.repo.save_account(account)
    
    def get_valuation_history(self, account_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[ValuationRecord]:
        """특정 기간의 평가 기록 반환"""
        valuations = self.get_valuations(account_id)
        
        if start_date:
            valuations = [v for v in valuations if v.evaluation_date >= start_date]
        if end_date:
            valuations = [v for v in valuations if v.evaluation_date <= end_date]
            
        return valuations
    
    def get_trade_pairs(self, account_id: str) -> List[TradePair]:
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

    def get_asset_allocation_full(self) -> Dict[str, float]:
        """포트폴리오와 동일 규칙의 카테고리별 금액 (0인 항목 포함)."""
        return compute_asset_allocation_categories(self.list_accounts())

    def list_asset_snapshots(self) -> List[Dict[str, Any]]:
        return self.repo.get_asset_snapshots()

    def add_asset_snapshot(self, label: Optional[str] = None) -> Dict[str, Any]:
        """현재 자산 구성을 saving-point로 저장."""
        cats = self.get_asset_allocation_full()
        total = sum(cats.values())
        snapshot = {
            "id": gen_id(),
            "created_at": today_iso(),
            "label": (label or "").strip(),
            "categories": {k: float(cats.get(k, 0) or 0) for k in ASSET_CATEGORY_KEYS},
            "total": float(total),
        }
        self.repo.add_asset_snapshot(snapshot)
        return snapshot

    def delete_asset_snapshot(self, snapshot_id: str) -> bool:
        return self.repo.delete_asset_snapshot(snapshot_id)

    def get_asset_growth_comparison(self, baseline_snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """현재 자산 vs 선택한(또는 가장 최근) 저장 지점 — 카테고리·총액 증감·수익률."""
        snapshots = self.repo.get_asset_snapshots()
        if not snapshots:
            raise ValueError("비교할 저장 지점이 없습니다. 먼저 「지금 자산 저장」으로 저장 지점을 만드세요.")

        if baseline_snapshot_id:
            baseline_row = next((s for s in snapshots if s.get("id") == baseline_snapshot_id), None)
            if not baseline_row:
                raise ValueError("선택한 저장 지점을 찾을 수 없습니다.")
        else:
            baseline_row = max(snapshots, key=lambda s: s.get("created_at", ""))

        current = self.get_asset_allocation_full()
        current_total = sum(current.values())

        baseline_cats = baseline_row.get("categories") or {}
        baseline_total = float(baseline_row.get("total") or 0)
        if baseline_total <= 0:
            baseline_total = sum(float(baseline_cats.get(k, 0) or 0) for k in ASSET_CATEGORY_KEYS)

        by_category: Dict[str, Dict[str, Any]] = {}
        for k in ASSET_CATEGORY_KEYS:
            b = float(baseline_cats.get(k, 0) or 0)
            c = float(current.get(k, 0) or 0)
            delta = c - b
            ret_pct: Optional[float] = None if b <= 0 else (delta / b) * 100.0
            by_category[k] = {
                "baseline": b,
                "current": c,
                "delta": delta,
                "return_pct": ret_pct,
            }

        delta_total = current_total - baseline_total
        total_return_pct: Optional[float] = None if baseline_total <= 0 else (delta_total / baseline_total) * 100.0

        return {
            "baseline_snapshot": {
                "id": baseline_row.get("id"),
                "created_at": baseline_row.get("created_at"),
                "label": baseline_row.get("label") or "",
                "total": baseline_total,
            },
            "current": {
                "categories": {k: float(current.get(k, 0) or 0) for k in ASSET_CATEGORY_KEYS},
                "total": float(current_total),
            },
            "by_category": by_category,
            "total": {
                "baseline": baseline_total,
                "current": float(current_total),
                "delta": float(delta_total),
                "return_pct": total_return_pct,
            },
        }

    def get_stock_portfolio(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.repo.get_stock_portfolio()

    def add_stock_entry(
        self,
        person: str,
        category: str,
        market: str,
        name: str,
        amount: float,
    ) -> Dict[str, Any]:
        person_n = (person or "").strip()
        if person_n not in STOCK_PERSONS:
            raise ValueError("person은 민규 또는 하영만 가능합니다.")
        category_n = (category or "").strip()
        if category_n not in STOCK_CATEGORIES:
            raise ValueError("카테고리는 지수 / 섹터 ETF / 종목 중 하나여야 합니다.")
        market_n = (market or "").strip()
        if market_n not in STOCK_MARKETS:
            raise ValueError("시장은 국장 또는 미장이어야 합니다.")
        name_n = (name or "").strip()
        if not name_n:
            raise ValueError("종목명을 입력하세요.")
        if amount <= 0:
            raise ValueError("금액(amount)은 0보다 커야 합니다.")

        entry = {
            "id": gen_id(),
            "person": person_n,
            "category": category_n,
            "market": market_n,
            "name": name_n,
            "amount": float(amount),
            "created_at": today_iso(),
        }
        self.repo.add_stock_entry(person_n, entry)
        return entry

    def delete_stock_entry(self, person: str, entry_id: str) -> bool:
        person_n = (person or "").strip()
        if person_n not in STOCK_PERSONS:
            raise ValueError("person은 민규 또는 하영만 가능합니다.")
        return self.repo.delete_stock_entry(person_n, entry_id)
