import pytest

from api.user.user_api import UserAPI
from tests.base_test import BaseTest
from utils import APISuite, HTTPStatus


class TestPostUserAPI(BaseTest):
    API_SUITE = APISuite.USER

    @pytest.fixture
    def user_api(self) -> UserAPI:
        """Return an initialized user API client."""
        return UserAPI(self.api_client)

    @pytest.mark.parametrize("first_name, last_name", [("John", "Doe")])
    def test_post_a_new_user_returns_id(
        self, first_name: str, last_name: str, user_api: UserAPI
    ) -> None:
        """Verify that Posting a new user creates a new user."""
        self.logger.log(
            f"Creating a new user with user first name: {first_name}, last name: {last_name}"
        )

        new_user = {"firstName": first_name, "lastName": last_name}

        response = user_api.create_a_new_user(user=new_user)

        assert response.status_code == HTTPStatus.CREATED.value, (
            f"Expected status code {HTTPStatus.CREATED.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        created_user = response.json()

        for field in ("id", "firstName", "lastName"):
            assert field in created_user, f"Expected '{field}' in user response"

        assert isinstance(created_user["id"], int), (
            f"Expected to get an integer user ID, got {type(created_user['id'])}"
        )

        assert created_user["firstName"] == first_name, (
            f"Expected to get user first name '{first_name}', got '{created_user['firstName']}'"
        )

        assert created_user["lastName"] == last_name, (
            f"Expected to get user last name = {last_name}, got {created_user['lastName']}"
        )

        self.logger.log("Successfully created a new user")
