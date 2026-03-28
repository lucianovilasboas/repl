"""Tests for calculate and stack endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── Execute ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_simple(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/execute",
        json={"input": "3 4 +"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["stack_depth"] == 1
    assert data["stack"][0]["value"] == 7.0
    assert data["error"] is None


@pytest.mark.asyncio
async def test_execute_multiple_values(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/execute",
        json={"input": "10 20 30"},
        headers=auth_headers,
    )
    data = resp.json()
    assert data["stack_depth"] == 3


@pytest.mark.asyncio
async def test_execute_error(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/execute",
        json={"input": "+"},
        headers=auth_headers,
    )
    data = resp.json()
    assert data["error"] is not None


@pytest.mark.asyncio
async def test_execute_persistence(client: AsyncClient, auth_headers, session_id):
    """Values persist across requests."""
    await client.post(f"/sessions/{session_id}/execute", json={"input": "5"}, headers=auth_headers)
    await client.post(f"/sessions/{session_id}/execute", json={"input": "10"}, headers=auth_headers)
    resp = await client.post(f"/sessions/{session_id}/execute", json={"input": "+"}, headers=auth_headers)
    data = resp.json()
    assert data["stack_depth"] == 1
    assert data["stack"][0]["value"] == 15.0


@pytest.mark.asyncio
async def test_execute_complex_expression(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/execute",
        json={"input": "3 4 + DUP *"},
        headers=auth_headers,
    )
    data = resp.json()
    assert data["stack"][0]["value"] == 49.0


@pytest.mark.asyncio
async def test_execute_variables(client: AsyncClient, auth_headers, session_id):
    await client.post(f"/sessions/{session_id}/execute", json={"input": "42 'X' STO"}, headers=auth_headers)
    resp = await client.post(f"/sessions/{session_id}/execute", json={"input": "X"}, headers=auth_headers)
    data = resp.json()
    assert data["stack"][0]["value"] == 42.0


# ── Undo ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_undo(client: AsyncClient, auth_headers, session_id):
    await client.post(f"/sessions/{session_id}/execute", json={"input": "5 10"}, headers=auth_headers)
    await client.post(f"/sessions/{session_id}/execute", json={"input": "+"}, headers=auth_headers)
    # Undo the addition
    resp = await client.post(f"/sessions/{session_id}/undo", headers=auth_headers)
    data = resp.json()
    assert data["stack_depth"] == 2
    assert data["error"] is None


@pytest.mark.asyncio
async def test_undo_empty(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(f"/sessions/{session_id}/undo", headers=auth_headers)
    data = resp.json()
    assert data["error"] is not None


# ── Stack manipulation ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_stack(client: AsyncClient, auth_headers, session_id):
    await client.post(f"/sessions/{session_id}/execute", json={"input": "1 2 3"}, headers=auth_headers)
    resp = await client.get(f"/sessions/{session_id}/stack", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 3
    assert items[0]["level"] == 3  # bottom
    assert items[2]["level"] == 1  # top


@pytest.mark.asyncio
async def test_push_number(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/stack/push",
        json={"value": 42, "type": "number"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["stack_depth"] == 1
    assert resp.json()["stack"][0]["value"] == 42.0


@pytest.mark.asyncio
async def test_push_string(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/stack/push",
        json={"value": "hello", "type": "string"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["stack"][0]["type"] == "string"


@pytest.mark.asyncio
async def test_push_vector(client: AsyncClient, auth_headers, session_id):
    resp = await client.post(
        f"/sessions/{session_id}/stack/push",
        json={"value": [1, 2, 3], "type": "vector"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["stack"][0]["type"] == "vector"


@pytest.mark.asyncio
async def test_clear_stack(client: AsyncClient, auth_headers, session_id):
    await client.post(f"/sessions/{session_id}/execute", json={"input": "1 2 3"}, headers=auth_headers)
    resp = await client.delete(f"/sessions/{session_id}/stack", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["stack_depth"] == 0
