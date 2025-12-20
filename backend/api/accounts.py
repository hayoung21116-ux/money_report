from fastapi import APIRouter, HTTPException, Depends
from typing import List
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

@router.get("/", response_model=List[Account])
async def list_accounts(service: LedgerService = Depends(get_ledger_service)):
    """Get all accounts"""
    accounts = service.list_accounts()
    # Debug: Print account colors
    for account in accounts:
        print(f"API endpoint - Account: {account.name}, Color: {account.color}")
    return accounts
