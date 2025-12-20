import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from models.domain import Account, Transaction, ValuationRecord

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
            default_data = {"accounts": [], "salaries": []}
            self._save_data(default_data)
            return default_data
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load data from {self.filepath}: {str(e)}")
            return {"accounts": [], "salaries": []}
    
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
                cash_holding=acc_dict.get("cash_holding", 0.0),
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
        salary = {
            "amount": amount,
            "month": month,
            "person": person
        }
        # Only add classification if it's provided
        if classification is not None:
            salary["classification"] = classification
        self.data.setdefault("salaries", []).append(salary)
        self._save_data(self.data)
    
    def update_salary(self, index: int, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Update salary data by index"""
        if 0 <= index < len(self.data.get("salaries", [])):
            self.data["salaries"][index] = {
                "amount": amount,
                "month": month,
                "person": person
            }
            # Only add classification if it's provided
            if classification is not None:
                self.data["salaries"][index]["classification"] = classification
            self._save_data(self.data)
    
    def delete_salary(self, index: int) -> None:
        """Delete salary data by index"""
        if 0 <= index < len(self.data.get("salaries", [])):
            self.data["salaries"].pop(index)
            self._save_data(self.data)
