from fastapi import APIRouter, HTTPException, Depends
from typing import List, Literal
from pydantic import BaseModel
from models.domain import Account, Transaction, ValuationRecord
from core.service import LedgerService
from database.json_database import JSONDatabase
from core.repository import LedgerRepository

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Dependency injection for service
def get_ledger_service():
    database = JSONDatabase()
    repository = LedgerRepository(database)
    service = LedgerService(repository)
    return service

@router.get("", response_model=List[Account])
@router.get("/", response_model=List[Account], include_in_schema=False)
async def list_accounts(service: LedgerService = Depends(get_ledger_service)):
    """Get all accounts"""
    accounts = service.list_accounts()
    # Debug: Print account colors
    for account in accounts:
        print(f"API endpoint - Account: {account.name}, Color: {account.color}")
    return accounts

@router.get("/{account_id}", response_model=Account)
async def get_account(account_id: str, service: LedgerService = Depends(get_ledger_service)):
    """Get account by ID"""
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/{account_id}/transactions", response_model=List[Transaction])
async def list_transactions(account_id: str, ascending: bool = False, service: LedgerService = Depends(get_ledger_service)):
    """Get transactions for an account"""
    return service.list_transactions(account_id, ascending)

class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    amount: float
    category: str
    memo: str = ""
    date: str

class TransactionUpdate(BaseModel):
    type: Literal["income", "expense"]
    amount: float
    category: str
    memo: str = ""
    date: str

@router.post("/{account_id}/transactions", response_model=Transaction)
async def add_transaction(account_id: str, transaction_data: TransactionCreate, service: LedgerService = Depends(get_ledger_service)):
    """Add a new transaction to an account"""
    try:
        return service.add_transaction(
            account_id=account_id,
            type_=transaction_data.type,
            amount=transaction_data.amount,
            category=transaction_data.category,
            memo=transaction_data.memo,
            date=transaction_data.date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{account_id}/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(account_id: str, transaction_id: str, transaction_data: TransactionUpdate, service: LedgerService = Depends(get_ledger_service)):
    """Update an existing transaction"""
    try:
        return service.update_transaction(
            account_id=account_id,
            transaction_id=transaction_id,
            type_=transaction_data.type,
            amount=transaction_data.amount,
            category=transaction_data.category,
            memo=transaction_data.memo,
            date=transaction_data.date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class AccountCreate(BaseModel):
    name: str
    type: Literal["현금", "투자", "소비"]
    color: str
    opening_balance: float = 0
    image_path: str = ""

class AccountUpdate(BaseModel):
    name: str
    type: Literal["현금", "투자", "소비"]
    color: str
    image_path: str = ""
    # For regular accounts
    opening_balance: float = 0
    # For investment accounts
    purchase_amount: float = 0.0
    cash_holding: float = 0.0
    evaluated_amount: float = 0.0

@router.post("", response_model=Account)
@router.post("/", response_model=Account, include_in_schema=False)
async def create_account(account_data: AccountCreate, service: LedgerService = Depends(get_ledger_service)):
    """Create a new account"""
    try:
        return service.add_account(
            name=account_data.name,
            type_=account_data.type,
            color=account_data.color,
            opening_balance=account_data.opening_balance,
            image_path=account_data.image_path
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{account_id}", response_model=Account)
async def update_account(account_id: str, account_data: AccountUpdate, service: LedgerService = Depends(get_ledger_service)):
    """Update an existing account"""
    try:
        # Get existing account
        account = service.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Update account fields
        account.name = account_data.name
        account.type = account_data.type
        account.color = account_data.color
        account.image_path = account_data.image_path
        
        # Update type-specific fields
        if account_data.type == "투자":
            account.purchase_amount = account_data.purchase_amount
            account.cash_holding = account_data.cash_holding
            # Update evaluated_amount from form data
            account.evaluated_amount = account_data.evaluated_amount
            # Update compatibility field for last_valuation_date if there are valuations
            if account.valuations:
                latest = account.latest_valuation
                if latest:
                    account.last_valuation_date = latest.evaluation_date[:10]
            else:
                account.last_valuation_date = ""
        else:
            account.opening_balance = account_data.opening_balance
        
        # Save the updated account
        service.update_account(account)
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
