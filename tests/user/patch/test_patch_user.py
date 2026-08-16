import pytest

from api.user.user_api import UserAPI
from tests.base_test import BaseTest
from utils import APISuite, HTTPStatus


class TestPatchUserAPI(BaseTest):
    API_SUITE = APISuite.USER

    @pytest.fixture
    def user_api(self) -> UserAPI:
        """Return an initialized user API client."""
        return UserAPI(self.api_client)

    @pytest.mark.parametrize("user_id, first_name", [(1, "Jane")])
    def test_patch_existing_user_updates_only_first_name(
        self, user_api: UserAPI, user_id: int, first_name: str
    ) -> None:
        """Verify that updating the first name field will not affect the other user fields."""
        self.logger.log(f"Getting the original user with ID={user_id}")

        original_response = user_api.get_user_by_id(user_id=user_id)

        assert original_response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {original_response.status_code}"
        )

        assert "application/json" in original_response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        original_user = original_response.json()

        assert original_user["firstName"] != first_name, (
            f"Test data error: user already has firstName {first_name!r}"
        )

        self.logger.log(
            f"Updating an existing user with user id ={user_id}, new first name ={first_name}"
        )

        updated_user_fields = {
            "firstName": first_name,
        }

        update_response = user_api.update_user_partially(user_id=user_id, user=updated_user_fields)

        assert update_response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {update_response.status_code}"
        )

        assert "application/json" in update_response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        updated_user = update_response.json()

        for field in ("id", "firstName", "lastName", "email"):
            assert field in updated_user, f"Expected '{field}' in user response"

        assert updated_user["id"] == user_id, (
            f"Expected to get user id '{user_id}', got '{updated_user['id']}'"
        )

        assert updated_user["firstName"] == first_name, (
            f"Expected to update user first name '{first_name}', got '{updated_user['firstName']}'"
        )

        assert updated_user["lastName"] == original_user["lastName"], (
            f"Expected to get origin user last name '{original_user['lastName']}', got '{updated_user['lastName']}'"
        )

        assert updated_user["email"] == original_user["email"], (
            f"Expected to get origin user email = {original_user['email']}, got {updated_user['email']}"
        )

        self.logger.log(
            "Successfully updated the user first name without affecting the other user fields."
        )
