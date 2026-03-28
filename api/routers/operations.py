"""Operations discovery router — public, no auth required."""

from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import OperationInfo, OperationCategory
from api.calculator import get_op_catalog

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/categories", response_model=List[OperationCategory])
async def list_categories():
    catalog = get_op_catalog()
    cats: Dict[str, List[str]] = {}
    for name, meta in catalog.items():
        cats.setdefault(meta["category"], []).append(name)
    return [
        OperationCategory(name=cat, count=len(ops), operations=sorted(ops))
        for cat, ops in sorted(cats.items())
    ]


@router.get("", response_model=List[OperationInfo])
async def list_operations(
    category: Optional[str] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search by name substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    catalog = get_op_catalog()
    items = []
    for name, meta in sorted(catalog.items()):
        if category and meta["category"] != category:
            continue
        if q and q.upper() not in name.upper() and not any(q.upper() in a for a in meta["aliases"]):
            continue
        items.append(OperationInfo(
            name=name, aliases=meta["aliases"],
            category=meta["category"], description=meta["description"],
        ))
    return items[skip: skip + limit]


@router.get("/{name}", response_model=OperationInfo)
async def get_operation(name: str):
    catalog = get_op_catalog()
    key = name.upper()
    # Direct match
    if key in catalog:
        meta = catalog[key]
        return OperationInfo(name=key, **meta)
    # Alias match
    for canonical, meta in catalog.items():
        if key in meta["aliases"]:
            return OperationInfo(name=canonical, **meta)
    raise HTTPException(status_code=404, detail=f"Operation '{name}' not found")
