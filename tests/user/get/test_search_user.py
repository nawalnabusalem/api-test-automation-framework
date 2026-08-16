import pytest

from api.user.user_api import UserAPI
from tests.base_test import BaseTest
from utils import APISuite, HTTPStatus


class TestSearchUserAPI(BaseTest):
    API_SUITE = APISuite.USER

    @pytest.fixture
    def user_api(self) -> UserAPI:
        """Return an initialized user API client."""
        return UserAPI(self.api_client)

    @pytest.mark.parametrize("search_query", ["John"])
    @pytest.mark.regression
    def test_search_user_by_query_returns_expected_user_list(
        self,
        user_api: UserAPI,
        search_query: str,
    ) -> None:
        """Verify that retrieving users by query returns the expected users list."""
        self.logger.log(f"Searching for users with query '{search_query}'")

        response = user_api.search_user_by_query(search_query=search_query)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        response_data = response.json()

        assert "users" in response_data, 'Expected field "users" not found in response'

        users = response_data.get("users", [])

        assert len(users) > 0, f'Expected to have at least 1 user matching query "{search_query}"'

        for user in users:
            searchable_text = " ".join(
                [
                    str(user.get("firstName", "")),
                    str(user.get("lastName", "")),
                    str(user.get("email", "")),
                    str(user.get("username", "")),
                ]
            )
            assert search_query.lower() in searchable_text.lower(), (
                f"user ID {user.get('id')} did not match query {search_query}"
            )

        self.logger.log(
            f"Successfully retrieved {len(users)} users with search query '{search_query}'"
        )
