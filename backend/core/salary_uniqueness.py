"""Single place for salary (month, person, classification) uniqueness rules."""
from typing import Any, Dict, List, Literal, Optional


def salary_classification_bucket(classification: Optional[str]) -> Literal["월급", "보너스"]:
    """Stored rows: only '보너스' is distinct; everything else counts as 월급 (matches Stats UI)."""
    return "보너스" if classification == "보너스" else "월급"


def parse_classification_for_write(classification: Optional[str]) -> Literal["월급", "보너스"]:
    if classification is None or classification == "":
        return "월급"
    if classification in ("월급", "보너스"):
        return classification  # type: ignore[return-value]
    raise ValueError('구분(classification)은 "월급" 또는 "보너스"만 사용할 수 있습니다.')


def normalize_salary_month(month: str) -> str:
    """Canonical YYYY-MM so 2026-4 and 2026-04 match; unknown shapes returned stripped."""
    raw = (month or "").strip()
    if not raw:
        return raw
    parts = raw.split("-")
    if len(parts) >= 2:
        try:
            y = int(parts[0].strip())
            mo = int(parts[1].strip())
            if 1000 <= y <= 9999 and 1 <= mo <= 12:
                return f"{y:04d}-{mo:02d}"
        except ValueError:
            pass
    return raw


def normalize_salary_person(person: str) -> str:
    return (person or "").strip()


def assert_unique_salary_record(
    rows: List[Dict[str, Any]],
    month: str,
    person: str,
    classification_key: Literal["월급", "보너스"],
    skip_index: Optional[int] = None,
) -> None:
    """At most one 월급 bucket and one 보너스 per (month, person), after normalization."""
    month_n = normalize_salary_month(month)
    person_n = normalize_salary_person(person)
    for i, row in enumerate(rows):
        if skip_index is not None and i == skip_index:
            continue
        if normalize_salary_month(str(row.get("month", ""))) != month_n:
            continue
        if normalize_salary_person(str(row.get("person", ""))) != person_n:
            continue
        existing = salary_classification_bucket(row.get("classification"))
        if existing == classification_key:
            label = "보너스" if classification_key == "보너스" else "월급"
            raise ValueError(
                f'해당 월({month_n})에 {person_n}의 {label} 항목이 이미 있습니다. '
                "같은 달·같은 사람에 월급과 보너스는 각각 한 건만 등록할 수 있습니다."
            )
