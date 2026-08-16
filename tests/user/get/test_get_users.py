import pytest

from api.user.user_api import UserAPI
from tests.base_test import BaseTest
from utils import APISuite, HTTPStatus


class TestGetUserAPI(BaseTest):
    """Test suite for user API GET endpoint."""

    API_SUITE = APISuite.USER

    @pytest.fixture
    def user_api(self) -> UserAPI:
        """Return an initialized user API client."""
        return UserAPI(self.api_client)

    @pytest.mark.smoke
    @pytest.mark.critical
    def test_get_all_users_returns_non_empty_list(
        self,
        user_api: UserAPI,
    ) -> None:
        """Verify that the Get All users returns a successful response with at least one user."""

        self.logger.log("Sending request to retrieve all users.")

        response = user_api.get_all_users()

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        response_data = response.json()
        users = response_data.get("users", [])

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )
        assert "users" in response_data, "Expected to get users JSON list"
        assert users, "Expected at least one user."
        assert "total" in response_data and response_data["total"] > 0, (
            f"Expected to get a positive total users, got {response_data.get('total')}"
        )
        assert len(users) <= response_data["limit"], (
            f"Expected to get users less than or equal{response_data['limit']},Actual users length= {len(users)}, limit = {response_data['limit']}"
        )

        for user in users:
            for field in ("id", "email", "firstName", "lastName"):
                assert field in user, f"Expected field {field} in user {user}"

            assert user["email"].strip(), (
                f'For user id "{user["id"]}" expected non empty email {user["email"]}'
            )
            assert user["firstName"].strip(), (
                f'For user id "{user["id"]}" expected non empty first name {user["firstName"]}'
            )
            assert user["lastName"].strip(), (
                f'For user id "{user["id"]}" expected non empty last name {user["lastName"]}'
            )

        self.logger.log(f"Retrieved {len(users)} users.")

    @pytest.mark.parametrize("user_id", [1])
    @pytest.mark.critical
    def test_get_user_by_id_returns_expected_user(
        self,
        user_api: UserAPI,
        user_id: int,
    ) -> None:
        """Verify that retrieving a user by ID returns the expected user."""
        self.logger.log(f"Retrieving the user with ID={user_id}")
        response = user_api.get_user_by_id(user_id=user_id)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        user = response.json()

        assert user, "Expected a user in the response."

        for field in ("id", "email", "firstName", "lastName"):
            assert field in user, f"Expected '{field}' in user response"

        assert user["id"] == user_id, f"Expected user ID {user_id}, got {user['id']}"
        assert user["email"].strip(), (
            f'For user id "{user["id"]}" expected non empty email {user["email"]}'
        )
        assert "@" in user["email"], (
            f'For user id "{user["id"]}" expected a formatted email address(e,g a@a.com), got "{user["email"]}"'
        )
        assert user["firstName"].strip(), (
            f'For user id "{user["id"]}" expected non empty first name {user["firstName"]}'
        )
        assert user["lastName"].strip(), (
            f'For user id "{user["id"]}" expected non empty last name {user["lastName"]}'
        )

        self.logger.log(
            f"Successfully retrieved user: ID={user['id']}, first_name={user['firstName']}"
        )

    @pytest.mark.parametrize("user_id", [9999, 0, -3])
    @pytest.mark.negative
    def test_get_user_by_invalid_id_returns_not_found(
        self,
        user_id: int,
        user_api: UserAPI,
    ) -> None:
        """Verify that requesting a non-existent user ID returns a 404 response with an appropriate error message."""

        self.logger.log(f"Retrieving user with invalid ID={user_id}")

        response = user_api.get_user_by_id(user_id=user_id)

        assert response.status_code == HTTPStatus.NOT_FOUND.value, (
            f"Expected status code {HTTPStatus.NOT_FOUND.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        error = response.json()
        assert "message" in error, "Expected error message in response body"
        assert error["message"].strip(), "Expected non empty error message in response body"

        message = error["message"].lower()
        assert "not found" in message or str(user_id) in message, (
            f"Invalid error message format , returned error message: {message}"
        )

        self.logger.log(f"Received expected error for user ID={user_id}: {error['message']}")
