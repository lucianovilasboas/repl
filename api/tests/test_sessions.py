"""Tests for session CRUD endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, auth_headers):
    resp = await client.post("/sessions", json={"name": "my_calc"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my_calc"
    assert data["stack_depth"] == 0


@pytest.mark.asyncio
async def test_create_session_default_name(client: AsyncClient, auth_headers):
    resp = await client.post("/sessions", headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "default"


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, auth_headers):
    await client.post("/sessions", json={"name": "s1"}, headers=auth_headers)
    await client.post("/sessions", json={"name": "s2"}, headers=auth_headers)
    resp = await client.get("/sessions", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_session_detail(client: AsyncClient, auth_headers, session_id):
    resp = await client.get(f"/sessions/{session_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == session_id
    assert data["stack"] == []
    assert data["variables"] == {}
    assert "settings" in data


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient, auth_headers, session_id):
    resp = await client.delete(f"/sessions/{session_id}", headers=auth_headers)
    assert resp.status_code == 204
    resp2 = await client.get(f"/sessions/{session_id}", headers=auth_headers)
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_reset_session(client: AsyncClient, auth_headers, session_id):
    # Push some values first
    await client.post(f"/sessions/{session_id}/execute", json={"input": "1 2 3"}, headers=auth_headers)
    # Reset
    resp = await client.post(f"/sessions/{session_id}/reset", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["stack_depth"] == 0


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient, auth_headers, session_id):
    resp = await client.patch(
        f"/sessions/{session_id}/settings",
        json={"angle_mode": "DEG", "num_format": "FIX", "fix_digits": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["angle_mode"] == "DEG"
    assert data["num_format"] == "FIX"
    assert data["fix_digits"] == 2


@pytest.mark.asyncio
async def test_session_not_found(client: AsyncClient, auth_headers):
    resp = await client.get("/sessions/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_session_requires_auth(client: AsyncClient):
    resp = await client.get("/sessions")
    assert resp.status_code in (401, 403)
