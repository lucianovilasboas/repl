"""Tests for auth endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "username": "newuser", "email": "new@test.com", "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@test.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"username": "dup", "email": "dup@test.com", "password": "secret123"}
    resp1 = await client.post("/auth/register", json=payload)
    assert resp1.status_code == 201
    resp2 = await client.post("/auth/register", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/auth/register", json={
        "username": "login_user", "email": "login@test.com", "password": "pass123",
    })
    resp = await client.post("/auth/login", json={
        "username": "login_user", "password": "pass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={
        "username": "wp_user", "email": "wp@test.com", "password": "correct",
    })
    resp = await client.post("/auth/login", json={
        "username": "wp_user", "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/auth/register", json={
        "username": "ref_user", "email": "ref@test.com", "password": "pass123",
    })
    login = await client.post("/auth/login", json={
        "username": "ref_user", "password": "pass123",
    })
    refresh_token = login.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_invalid_refresh_token(client: AsyncClient):
    resp = await client.post("/auth/refresh", json={"refresh_token": "bogus"})
    assert resp.status_code == 401
