"""Tests for operations discovery endpoints (public, no auth)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    resp = await client.get("/operations/categories")
    assert resp.status_code == 200
    cats = resp.json()
    assert len(cats) > 0
    names = [c["name"] for c in cats]
    assert "arithmetic" in names
    assert "scientific" in names


@pytest.mark.asyncio
async def test_list_operations(client: AsyncClient):
    resp = await client.get("/operations")
    assert resp.status_code == 200
    ops = resp.json()
    assert len(ops) > 50  # we have 130+ operations


@pytest.mark.asyncio
async def test_filter_by_category(client: AsyncClient):
    resp = await client.get("/operations", params={"category": "arithmetic"})
    assert resp.status_code == 200
    ops = resp.json()
    assert all(op["category"] == "arithmetic" for op in ops)
    assert len(ops) > 0


@pytest.mark.asyncio
async def test_search_operations(client: AsyncClient):
    resp = await client.get("/operations", params={"q": "SIN"})
    assert resp.status_code == 200
    ops = resp.json()
    assert any("SIN" in op["name"] or any("SIN" in a for a in op["aliases"]) for op in ops)


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    resp1 = await client.get("/operations", params={"limit": 5})
    resp2 = await client.get("/operations", params={"limit": 5, "skip": 5})
    assert len(resp1.json()) == 5
    assert len(resp2.json()) == 5
    assert resp1.json()[0]["name"] != resp2.json()[0]["name"]


@pytest.mark.asyncio
async def test_get_operation_by_name(client: AsyncClient):
    resp = await client.get("/operations/+")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "arithmetic"


@pytest.mark.asyncio
async def test_get_operation_not_found(client: AsyncClient):
    resp = await client.get("/operations/NONEXISTENT_OP_XYZ")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()
