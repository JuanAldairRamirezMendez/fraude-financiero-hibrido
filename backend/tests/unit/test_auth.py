from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

from app.core.security import (
    UserPrincipal,
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.core.settings import Settings
from app.main import create_app


def test_password_and_refresh_hashes() -> None:
    password_hash = hash_password("secret-password")
    assert password_hash != "secret-password"
    assert verify_password("secret-password", password_hash)
    assert not verify_password("wrong-password", password_hash)
    token = new_refresh_token()
    assert token != hash_refresh_token(token)
    assert len(hash_refresh_token(token)) == 64


def test_access_token_round_trip_and_rejection() -> None:
    settings = Settings(environment="test", jwt_secret_key="a" * 40)
    user = UserPrincipal("user-1", "analyst", "analyst")
    token = create_access_token(user, settings)
    assert decode_access_token(token, settings) == user
    with pytest.raises(Exception):
        decode_access_token("not-a-token", settings)


def test_auth_settings_reject_weak_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(environment="test", auth_enabled=True, jwt_secret_key="weak")


def test_auth_http_flow_and_csrf() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        settings = Settings(
            environment="test",
            auth_enabled=True,
            jwt_secret_key="test-secret-key-with-at-least-32-bytes!",
            auth_bootstrap_username="analyst",
            auth_bootstrap_password="correct horse battery staple",
            fail_fast=False,
            seed_snapshot_alerts=False,
            expose_prometheus=False,
            database_url=f"sqlite:///{root / 'auth.db'}",
            model_path=root / "missing-model.pkl",
            preprocessor_path=root / "missing-preprocessor.joblib",
            feature_contract_path=root / "missing-contract.json",
            model_metadata_path=root / "missing-metadata.json",
            snapshot_path=root / "missing-snapshot.json",
            transactions_path=root / "missing-transactions.parquet",
            static_dir=root / "dist",
        )
        with TestClient(create_app(settings)) as client:
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "analyst", "password": "correct horse battery staple"},
            )
            assert login.status_code == 200
            assert login.json()["user"]["role"] == "analyst"
            refresh = client.cookies.get("refresh_token")
            csrf = client.cookies.get("csrf_token")
            assert refresh and csrf
            assert client.get("/api/v1/auth/me").json()["authenticated"]
            assert client.post("/api/v1/auth/refresh").status_code == 403
            rotated = client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf})
            assert rotated.status_code == 200
            assert client.cookies.get("refresh_token") != refresh
            csrf = client.cookies.get("csrf_token")
            assert csrf
            client.cookies.set("refresh_token", refresh)
            assert client.post(
                "/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf}
            ).status_code == 401
            assert client.post(
                "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}
            ).status_code == 204
            assert client.post(
                "/api/v1/auth/login", json={"username": "analyst", "password": "wrong"}
            ).status_code == 401
