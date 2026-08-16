import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestPatchProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize("product_id, new_stock", [(1, 50)])
    def test_patch_existing_product_updates_only_stock(
        self, product_id: int, new_stock: int, product_api: ProductAPI
    ) -> None:
        """Verify that updating the stock field will not affect the other product fields."""
        self.logger.info(f"Getting the origin of product with product id ={product_id}")

        original_response = product_api.get_product_by_id(product_id)

        assert original_response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {original_response.status_code}"
        )

        assert "application/json" in original_response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        original_product = original_response.json()

        self.logger.info(
            f"Updating an existing product with product id ={product_id}, new stock ={new_stock}"
        )

        updated_product_fields = {
            "stock": new_stock,
        }

        update_response = product_api.update_product_partially(
            product_id=product_id, product=updated_product_fields
        )

        assert update_response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {update_response.status_code}"
        )

        assert "application/json" in update_response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        updated_product = update_response.json()

        for field in ("id", "title", "price", "description", "category", "stock"):
            assert field in updated_product, f"Expected '{field}' in product response"

        assert updated_product["id"] == product_id, (
            f"Expected to get product id '{product_id}', got '{updated_product['id']}'"
        )

        assert updated_product["stock"] == new_stock, (
            f"Expected to update product stock '{new_stock}', got '{updated_product['stock']}'"
        )

        assert updated_product["title"] == original_product["title"], (
            f"Expected to get origin product title '{original_product['title']}', got '{updated_product['title']}'"
        )

        assert updated_product["price"] == original_product["price"], (
            f"Expected to get origin product price = {original_product['price']}, got {updated_product['price']}"
        )

        assert updated_product["category"] == original_product["category"], (
            f"Expected to get origin product category = {original_product['category']}, got {updated_product['category']}"
        )

        assert updated_product["description"] == original_product["description"], (
            f"Expected to get origin product description = {original_product['description']}, got {updated_product['description']}"
        )

        self.logger.info(
            msg="Successfully updated the stock product without affecting the other product fields."
        )
