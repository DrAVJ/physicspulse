import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from main import app
from db.models import Base
from db.session import get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestSession() as session:
            async with session.begin():
                yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    resp = await client.post("/auth/register", json={
        "email": "teacher@test.com",
        "password": "secret123",
        "name": "Test Teacher"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "teacher@test.com"

    # Login
    resp = await client.post("/auth/token", data={
        "username": "teacher@test.com",
        "password": "secret123"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token


@pytest.mark.asyncio
async def test_get_me(client):
    await client.post("/auth/register", json={
        "email": "me@test.com",
        "password": "pass123",
        "name": "Me Teacher"
    })
    login = await client.post("/auth/token", data={
        "username": "me@test.com",
        "password": "pass123"
    })
    token = login.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@test.com"
