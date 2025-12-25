from typing import List, Optional, Dict, Any
from models.domain import Account, Transaction, ValuationRecord
from database.json_database import JSONDatabase

class LedgerRepository:
    """Repository for managing account and transaction persistence"""
    
    def __init__(self, database: JSONDatabase):
        """Initialize with database"""
        self.db = database
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        return self.db.get_all_accounts()
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        accounts = self.get_all_accounts()
        for account in accounts:
            if account.id == account_id:
                return account
        return None
    
    def save_account(self, account: Account) -> None:
        """Save an account"""
        self.db.save_account(account)
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an account"""
        return self.db.delete_account(account_id)
    
    def add_transaction(self, account_id: str, transaction: Transaction) -> bool:
        """Add transaction to account"""
        account = self.get_account(account_id)
        if account:
            account.transactions.append(transaction)
            self.save_account(account)
            return True
        return False

    def update_transaction(self, account_id: str, transaction: Transaction) -> bool:
        """Update transaction in account"""
        account = self.get_account(account_id)
        if account:
            for i, t in enumerate(account.transactions):
                if t.id == transaction.id:
                    account.transactions[i] = transaction
                    self.save_account(account)
                    return True
        return False
    
    def add_valuation(self, account_id: str, valuation: ValuationRecord) -> bool:
        """Add valuation to account"""
        account = self.get_account(account_id)
        if account:
            account.valuations.append(valuation)
            # Update compatibility fields using the new calculated value
            account.evaluated_amount = account.calculated_evaluated_amount
            if account.valuations:
                latest = account.latest_valuation
                if latest:
                    account.last_valuation_date = latest.evaluation_date[:10]
            self.save_account(account)
            return True
        return False
    
    def get_salaries(self) -> List[Dict[str, Any]]:
        """Get all salary data"""
        return self.db.get_salaries()
    
    def add_salary(self, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Add salary data"""
        self.db.add_salary(amount, month, person, classification)
    
    def update_salary(self, index: int, amount: float, month: str, person: str, classification: Optional[str] = None) -> None:
        """Update salary data by index"""
        self.db.update_salary(index, amount, month, person, classification)
    
    def delete_salary(self, index: int) -> None:
        """Delete salary data by index"""
        self.db.delete_salary(index)
