import pytest

from api.user.user_api import UserAPI
from tests.base_test import BaseTest
from utils import APISuite, HTTPStatus


class TestPutUserAPI(BaseTest):
    API_SUITE = APISuite.USER

    @pytest.fixture
    def user_api(self) -> UserAPI:
        """Return an initialized user API client."""
        return UserAPI(self.api_client)

    @pytest.mark.parametrize(
        "user_id, new_first_name, new_last_name, new_email", [(1, "Luca", "Deo", "Luca@gmail.com")]
    )
    def test_put_existing_user_returns_updated_fields(
        self,
        user_id: int,
        new_first_name: str,
        new_last_name: str,
        new_email: str,
        user_api: UserAPI,
    ) -> None:
        """Verify that Putting an existing user replaces the user."""
        self.logger.log(
            f"Replacing an existing user with user_id={user_id}, with new fields -- "
            f"first name: {new_first_name}, last name: {new_last_name}, email: {new_email}."
        )

        new_user = {"firstName": new_first_name, "lastName": new_last_name, "email": new_email}

        response = user_api.replace_user(user_id=user_id, user=new_user)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        replaced_user = response.json()

        for field in ("id", "firstName", "lastName", "email"):
            assert field in replaced_user, f"Expected '{field}' in user response"

        assert replaced_user["id"] == user_id, (
            f"Expected to get user id '{user_id}', got '{replaced_user['id']}'"
        )

        assert replaced_user["firstName"] == new_first_name, (
            f"Expected to update user first name '{new_first_name}', got '{replaced_user['firstName']}'"
        )

        assert replaced_user["lastName"] == new_last_name, (
            f"Expected to update user last name = {new_last_name}, got {replaced_user['lastName']}"
        )

        assert replaced_user["email"] == new_email, (
            f"Expected to update user email = {new_email}, got {replaced_user['email']}"
        )

        self.logger.log("Successfully updated the user using PUT")
