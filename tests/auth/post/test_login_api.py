import pytest

from api.auth.auth_api import AuthAPI
from config.config import Config
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestLoginAPI(BaseTest):
    @pytest.fixture
    def auth_api(self) -> AuthAPI:
        """Return an initialized auth API client."""
        return AuthAPI(self.api_client)

    @pytest.mark.parametrize(
        "credentials",
        [{"username": Config.USERNAME, "password": Config.PASSWORD}],
        ids=["valid user credentials"],
    )
    def test_login_with_valid_credentials(
        self, credentials: dict[str, str], auth_api: AuthAPI
    ) -> None:
        """Verify that login with valid credentials will return a valid token."""
        self.logger.info(
            f"Verifying login with valid credentials for {credentials.get('username')}"
        )

        response = auth_api.login_with_credentials(credentials=credentials)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        user_data = response.json()

        for field in (
            "id",
            "username",
            "email",
            "firstName",
            "lastName",
            "accessToken",
            "refreshToken",
        ):
            assert field in user_data, f"Expected '{field}' in login response"

        token_parts = user_data["accessToken"].split(".")

        assert len(token_parts) == 3, (
            "Expected accessToken to have JWT format: header.payload.signature"
        )

        assert all(token_parts), "Expected for accessToken, every JWT section to be non-empty"

        self.logger.info(
            f"Successful login with a valid credentials for {credentials.get('username')}"
        )

    @pytest.mark.parametrize(
        "credentials",
        [
            {"username": "wrong_username", "password": "wrong_password"},
            {"username": Config.USERNAME},
            {"password": Config.PASSWORD},
        ],
        ids=["wrong username and password", "missing password", "missing username"],
    )
    def test_login_with_invalid_credentials(
        self, credentials: dict[str, str], auth_api: AuthAPI
    ) -> None:
        """Verify that login with invalid credentials will return an error message and not login."""
        self.logger.info(
            f"Verifying login with invalid credentials {credentials.get('username', 'missing user name')}"
        )

        response = auth_api.login_with_credentials(credentials=credentials)

        assert response.status_code == HTTPStatus.BAD_REQUEST.value, (
            f"Expected status code {HTTPStatus.BAD_REQUEST.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        response_data = response.json()

        assert "message" in response_data, (
            "Expected 'message' in login with invalid credentials login response"
        )
        assert response_data["message"], (
            "Expected non empty message in login with invalid credentials login response"
        )

        assert "accessToken" not in response_data, (
            "Expected 'accessToken' is not in login with invalid credentials login response"
        )
        assert "refreshToken" not in response_data, (
            "Expected 'refreshToken' is not in login with invalid credentials login response"
        )

        self.logger.info("Successfully failed to login with invalid credentials.")
