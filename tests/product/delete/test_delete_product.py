import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestDeleteProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize("product_id", [1])
    def test_delete_existing_product_returns_deleted_product(
        self, product_id: int, product_api: ProductAPI
    ) -> None:
        """Verify Delete an existing product."""

        self.logger.info(f"Deleting an existing product with product id= {product_id}.")
        response = product_api.delete_product_by_id(product_id=product_id)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        deleted_product = response.json()

        assert deleted_product["id"] == product_id, (
            f"Expected deleted product ID {product_id}, got {deleted_product.get('id')}"
        )

        assert deleted_product.get("isDeleted") is True, "Expected 'isDeleted' to be exactly True"

        assert deleted_product.get("deletedOn"), "Expected a non-empty 'deletedOn' timestamp"

        self.logger.info("Successfully Deleted the product.")
