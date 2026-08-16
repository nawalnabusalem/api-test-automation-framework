from typing import Any

from api.api_client import APIClient


class UserAPI:
    def __init__(self, client: APIClient):
        self.client = client
        self.endpoint = "users"

    def get_all_users(self):
        return self.client.get(f"{self.endpoint}")

    def get_user_by_id(self, user_id: int):
        return self.client.get(f"{self.endpoint}/{user_id}")

    def search_user_by_query(self, search_query: str):
        if not search_query.strip():
            raise ValueError("search query cannot be empty")

        return self.client.get(f"{self.endpoint}/search", params={"q": search_query})

    def create_a_new_user(self, user: dict[str, Any]):
        return self.client.post(f"{self.endpoint}/add", payload=user)

    def replace_user(self, user_id: int, user: dict[str, Any]):
        return self.client.put(f"{self.endpoint}/{user_id}", payload=user)

    def update_user_partially(self, user_id: int, user: dict[str, Any]):
        return self.client.patch(f"{self.endpoint}/{user_id}", payload=user)

    def delete_user(self, user_id: int):
        return self.client.delete(f"{self.endpoint}/{user_id}")
