from typing import Any

from api.api_client import APIClient


class ProductAPI:
    def __init__(self, client: APIClient):
        self.client = client
        self.endpoint = "products"

    def get_all_products(self):
        return self.client.get(f"{self.endpoint}")

    def get_product_by_id(self, product_id: int):
        return self.client.get(f"{self.endpoint}/{product_id}")

    def get_product_by_category(self, product_category: str):
        if not product_category.strip():
            raise ValueError("Product category cannot be empty")

        return self.client.get(f"{self.endpoint}/category/{product_category}")

    def get_product_pagination_list(self, limit: int, skip: int):
        return self.client.get(f"{self.endpoint}", params={"limit": limit, "skip": skip})

    def search_product_by_query(self, search_query: str):
        if not search_query.strip():
            raise ValueError("search query cannot be empty")

        return self.client.get(f"{self.endpoint}/search", params={"q": search_query})

    def create_a_new_product(self, product: dict[str, Any]):
        return self.client.post(f"{self.endpoint}/add", payload=product)

    def replace_product(self, product_id: int, product: dict[str, Any]):
        return self.client.put(f"{self.endpoint}/{product_id}", payload=product)

    def update_product_partially(self, product_id: int, product: dict[str, Any]):
        return self.client.patch(f"{self.endpoint}/{product_id}", payload=product)

    def delete_product_by_id(self, product_id: int):
        return self.client.delete(f"{self.endpoint}/{product_id}")
