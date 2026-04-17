from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
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


class SnapshotCreate(BaseModel):
    label: Optional[str] = None

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
    categories = service.get_asset_allocation_full()
    return {k: v for k, v in categories.items() if v > 0}


@router.get("/asset-snapshots")
async def list_asset_snapshots(service: LedgerService = Depends(get_ledger_service)):
    """저장 지점(saving-point) 목록 — 최신순."""
    return service.list_asset_snapshots()


@router.post("/asset-snapshots")
async def create_asset_snapshot(
    body: SnapshotCreate,
    service: LedgerService = Depends(get_ledger_service),
):
    """현재 포트폴리오를 저장 지점으로 기록."""
    return service.add_asset_snapshot(label=body.label)


@router.delete("/asset-snapshots/{snapshot_id}")
async def delete_asset_snapshot(snapshot_id: str, service: LedgerService = Depends(get_ledger_service)):
    ok = service.delete_asset_snapshot(snapshot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="저장 지점을 찾을 수 없습니다.")
    return {"message": "deleted"}


@router.get("/asset-growth")
async def get_asset_growth(
    baseline_id: Optional[str] = None,
    service: LedgerService = Depends(get_ledger_service),
):
    """현재 자산 vs 저장 지점(미지정 시 가장 최근 저장 지점) 비교."""
    try:
        return service.get_asset_growth_comparison(baseline_snapshot_id=baseline_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
