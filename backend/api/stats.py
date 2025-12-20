from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from models.domain import Account
from core.service import LedgerService
from database.json_database import JSONDatabase
from core.repository import LedgerRepository

router = APIRouter(prefix="/stats", tags=["statistics"])

# Dependency injection for service
def get_ledger_service():
    database = JSONDatabase()
    repository = LedgerRepository(database)
    service = LedgerService(repository)
    return service

@router.get("/total-assets")
async def get_total_assets(service: LedgerService = Depends(get_ledger_service)):
    """Get total assets"""
    return {"total_assets": service.total_assets()}

@router.get("/total-cash")
async def get_total_cash(service: LedgerService = Depends(get_ledger_service)):
    """Get total cash balance"""
    return {"total_cash": service.total_cash()}

@router.get("/monthly-income-breakdown")
async def get_monthly_income_breakdown(year: Optional[str] = None, service: LedgerService = Depends(get_ledger_service)):
    """Get monthly income breakdown"""
    return service.monthly_income_breakdown(year)

@router.get("/salaries")
async def get_salaries(year: Optional[str] = None, service: LedgerService = Depends(get_ledger_service)):
    """Get all salary data"""
    return service.get_salaries(year)

@router.post("/salaries")
async def add_salary(amount: float, month: str, person: str, classification: Optional[str] = None, service: LedgerService = Depends(get_ledger_service)):
    """Add salary data"""
    try:
        service.add_salary(amount, month, person, classification)
        return {"message": "Salary added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/salaries/{index}")
async def update_salary(index: int, amount: float, month: str, person: str, classification: Optional[str] = None, service: LedgerService = Depends(get_ledger_service)):
    """Update salary data by index"""
    try:
        service.update_salary(index, amount, month, person, classification)
        return {"message": "Salary updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/salaries/{index}")
async def delete_salary(index: int, service: LedgerService = Depends(get_ledger_service)):
    """Delete salary data by index"""
    try:
        service.delete_salary(index)
        return {"message": "Salary deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/salaries/median")
async def get_salary_median(year: Optional[str] = None, person: Optional[str] = None, service: LedgerService = Depends(get_ledger_service)):
    """Get the median of monthly salary totals"""
    median = service.calculate_salary_median(year=year, person=person)
    if median is None:
        return {"message": "No salary data available for median calculation"}
    return {"median_salary": median}

@router.get("/salaries/monthly-totals")
async def get_monthly_salary_totals(year: Optional[str] = None, person: Optional[str] = None, service: LedgerService = Depends(get_ledger_service)):
    """Get monthly salary totals, sorted in descending order of amount"""
    monthly_totals = service.get_monthly_salary_totals(year=year, person=person)
    
    # Sort by amount in descending order
    sorted_totals = sorted(monthly_totals.items(), key=lambda item: item[1], reverse=True)
    
    return {"monthly_totals": dict(sorted_totals)}

@router.get("/asset-allocation")
async def get_asset_allocation(service: LedgerService = Depends(get_ledger_service)):
    """Calculate the total value for each asset category"""
    categories = {
        "현금": 0.0,
        "부동산": 0.0,
        "비트코인": 0.0,
        "주식": 0.0,
        "기타": 0.0
    }
    accounts = service.list_accounts()
    
    for acc in accounts:
        if acc.status == "dead":
            continue
        
        value = acc.asset_value if acc.type == "투자" else acc.balance()

        if value <= 0:
            continue

        if acc.type == "투자":
            # This is an investment account, categorize it further
            # Categorize investment accounts by name or image path
            account_name_lower = acc.name.lower()
            image_path_lower = acc.image_path.lower() if acc.image_path else ""
            
            if "부동산" in account_name_lower or "부동산" in image_path_lower:
                categories["부동산"] += value
            elif "비트코인" in account_name_lower or "비트코인" in image_path_lower or "bitcoin" in image_path_lower:
                categories["비트코인"] += value
            elif any(keyword in account_name_lower or keyword in image_path_lower for keyword in ["주식", "증권", "나무", "한국투자", "ibk", "ok저축은행"]):
                categories["주식"] += value
            else:
                categories["기타"] += value
        else:
            # All other non-investment accounts are treated as cash
            categories["현금"] += value
    
    final_categories = {k: v for k, v in categories.items() if v > 0}
    return final_categories
