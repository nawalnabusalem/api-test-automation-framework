from typing import Any

from api.api_client import APIClient


class CartAPI:
    def __init__(self, client: APIClient):
        self.client = client
        self.endpoint = "carts"

    def get_all_carts(self):
        return self.client.get(f"{self.endpoint}")

    def get_cart_by_id(self, cart_id: int):
        return self.client.get(f"{self.endpoint}/{cart_id}")

    def get_cart_for_user(self, user_id: int):
        return self.client.get(f"{self.endpoint}/user/{user_id}")

    def create_a_new_cart(self, cart: dict[str, Any]):
        return self.client.post(f"{self.endpoint}/add", payload=cart)

    def delete_cart_by_id(self, cart_id: int):
        return self.client.delete(f"{self.endpoint}/{cart_id}")
