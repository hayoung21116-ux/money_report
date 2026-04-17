import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from models.domain import Account, Transaction, ValuationRecord, TradePair
from core.salary_uniqueness import (
    assert_unique_salary_record,
    normalize_salary_month,
    normalize_salary_person,
    parse_classification_for_write,
)

class JSONDatabase:
    """JSON file-based database implementation"""
    
    def __init__(self, filepath: str = "data/ledger.json"):
        """Initialize with path to JSON file"""
        self.filepath = Path(filepath)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        if not self.filepath.exists():
            # Create default data structure
            default_data = {"accounts": [], "salaries": [], "asset_snapshots": []}
            self._save_data(default_data)
            return default_data
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "asset_snapshots" not in data:
                data["asset_snapshots"] = []
            return data
        except Exception as e:
            print(f"Warning: Failed to load data from {self.filepath}: {str(e)}")
            return {"accounts": [], "salaries": [], "asset_snapshots": []}
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        try:
            # Create directory if it doesn't exist
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to save data to {self.filepath}: {str(e)}")
            raise
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts from database"""
        accounts = []
        for acc_dict in self.data.get("accounts", []):
            # Convert transactions
            transactions = [
                Transaction(**t) for t in acc_dict.get("transactions", [])
            ]
            
            # Convert valuations
            valuations = [
                ValuationRecord(**v) for v in acc_dict.get("valuations", [])
            ]
            
            # Create account with all data
            account = Account(
                id=acc_dict["id"],
                name=acc_dict["name"],
                type=acc_dict.get("type", "현금"),
                status=acc_dict.get("status", "active"),
                color=acc_dict["color"],
                opening_balance=acc_dict["opening_balance"],
                image_path=acc_dict.get("image_path", ""),
                purchase_amount=acc_dict.get("purchase_amount", 0.0),
                evaluated_amount=acc_dict.get("evaluated_amount", 0.0),
                last_valuation_date=acc_dict.get("last_valuation_date", ""),
                transactions=transactions,
                valuations=valuations
            )
            accounts.append(account)
        
        return accounts
 
    def get_salaries(self) -> List[Dict[str, Any]]:
        """Get all salary data"""
        return self.data.get("salaries", [])
    
    def add_salary(self, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Add salary data"""
        month_n = normalize_salary_month(month)
        person_n = normalize_salary_person(person)
        cls_key = parse_classification_for_write(classification)
        rows = self.data.setdefault("salaries", [])
        assert_unique_salary_record(rows, month_n, person_n, cls_key, skip_index=None)
        salary: Dict[str, Any] = {"amount": amount, "month": month_n, "person": person_n}
        if cls_key == "보너스":
            salary["classification"] = "보너스"
        rows.append(salary)
        self._save_data(self.data)
    
    def update_salary(self, index: int, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Update salary data by index"""
        salaries = self.data.get("salaries", [])
        if index < 0 or index >= len(salaries):
            raise ValueError("존재하지 않는 월급 항목입니다.")
        month_n = normalize_salary_month(month)
        person_n = normalize_salary_person(person)
        cls_key = parse_classification_for_write(classification)
        assert_unique_salary_record(salaries, month_n, person_n, cls_key, skip_index=index)
        row: Dict[str, Any] = {"amount": amount, "month": month_n, "person": person_n}
        if cls_key == "보너스":
            row["classification"] = "보너스"
        self.data["salaries"][index] = row
        self._save_data(self.data)
    
    def delete_salary(self, index: int) -> None:
        """Delete salary data by index"""
        if 0 <= index < len(self.data.get("salaries", [])):
            self.data["salaries"].pop(index)
            self._save_data(self.data)

    def save_account(self, account: Account) -> None:
        """Save an account"""
        accounts = self.data.get("accounts", [])
        
        # Convert account to dictionary
        account_dict = account.dict()
        
        # Check if account already exists
        for i, acc in enumerate(accounts):
            if acc["id"] == account.id:
                accounts[i] = account_dict
                self._save_data(self.data)
                return
        
        # Add new account
        accounts.append(account_dict)
        self.data["accounts"] = accounts
        self._save_data(self.data)

    def delete_account(self, account_id: str) -> bool:
        """Delete an account"""
        accounts = self.data.get("accounts", [])
        
        initial_len = len(accounts)
        accounts = [acc for acc in accounts if acc["id"] != account_id]
        
        if len(accounts) < initial_len:
            self.data["accounts"] = accounts
            self._save_data(self.data)
            return True
        return False

    def get_asset_snapshots(self) -> List[Dict[str, Any]]:
        """저장 지점 목록 (최신 created_at 우선)."""
        rows = list(self.data.get("asset_snapshots", []))
        return sorted(rows, key=lambda s: s.get("created_at", ""), reverse=True)

    def add_asset_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self.data.setdefault("asset_snapshots", []).append(snapshot)
        self._save_data(self.data)

    def delete_asset_snapshot(self, snapshot_id: str) -> bool:
        snaps = self.data.get("asset_snapshots", [])
        for i, s in enumerate(snaps):
            if s.get("id") == snapshot_id:
                snaps.pop(i)
                self._save_data(self.data)
                return True
        return False
