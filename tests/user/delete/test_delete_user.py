import pytest

from api.user.user_api import UserAPI
from tests.base_test import BaseTest
from utils import APISuite, HTTPStatus


class TestDeleteUserAPI(BaseTest):
    API_SUITE = APISuite.USER

    @pytest.fixture
    def user_api(self) -> UserAPI:
        """Return an initialized user API client."""
        return UserAPI(self.api_client)

    @pytest.mark.parametrize("user_id", [1])
    def test_delete_existing_user_returns_deleted_user(
        self, user_id: int, user_api: UserAPI
    ) -> None:
        """Verify Delete an existing user."""

        self.logger.log(f"Deleting existing user with ID={user_id}")
        response = user_api.delete_user(user_id=user_id)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        deleted_user = response.json()

        assert deleted_user["id"] == user_id, (
            f"Expected deleted user ID {user_id}, got {deleted_user.get('id')}"
        )

        assert deleted_user.get("isDeleted") is True, "Expected 'isDeleted' to be exactly True"

        assert deleted_user.get("deletedOn"), "Expected a non-empty 'deletedOn' timestamp"

        self.logger.log("Successfully deleted the user")
