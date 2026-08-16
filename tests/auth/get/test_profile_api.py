from typing import Any

import pytest

from api.auth.auth_api import AuthAPI
from config.config import Config
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestProfileAPI(BaseTest):
    @pytest.fixture
    def auth_api(self) -> AuthAPI:
        """Return an initialized auth API client."""
        return AuthAPI(self.api_client)

    @pytest.fixture
    def authenticated_user(self, auth_api: AuthAPI) -> dict[str, Any]:
        response = auth_api.login_with_credentials(
            credentials={"username": Config.USERNAME, "password": Config.PASSWORD}
        )

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        user_data = response.json()

        for field in ("id", "username", "email", "firstName", "lastName", "accessToken"):
            assert field in user_data, f"Expected '{field}' in authentication response"

        self.api_client.set_auth_token(token=user_data["accessToken"])

        return user_data

    def test_get_authenticated_user_profile(
        self, authenticated_user: dict[str, Any], auth_api: AuthAPI
    ) -> None:
        """Verify that the user profile has the same data as the authenticated user"""
        self.logger.info(
            f"Verifying the user profile has the same data as the authenticated for user: {authenticated_user['username']}"
        )

        response = auth_api.get_authenticated_user_profile()

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        profile_data = response.json()

        profile_fields = (
            "id",
            "username",
            "email",
            "firstName",
            "lastName",
        )

        for field in profile_fields:
            assert field in profile_data, f"Expected '{field}' in profile response"

        for field in profile_fields:
            assert profile_data[field] == authenticated_user[field], (
                f"Expected get user profile '{field}' equal to authenticated data,"
                f" got profile {field} = {profile_data[field]},"
                f"current authenticated data = {authenticated_user[field]}"
            )

        self.logger.info(
            f"Successfully get profile data for  authenticated user {authenticated_user.get('username')}"
        )
