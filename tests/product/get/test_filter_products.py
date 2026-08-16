import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestFilterProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize("category", ["beauty"])
    def test_filter_product_by_category_returns_expected_product_list(
        self,
        product_api: ProductAPI,
        category: str,
    ) -> None:
        """Verify that Filtering products by category returns the expected products list."""

        self.logger.info(msg=f"Filtering products by category '{category}'")

        response = product_api.get_product_by_category(product_category=category)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        response_data = response.json()
        products = response_data.get("products", [])

        assert "products" in response_data, "Expected to get products JSON list"

        assert len(products) > 0, (
            f'Expected to find products with category "{category}", Got 0 results'
        )

        for product in products:
            assert "category" in product, "Expected category in product response"
            assert category.lower() == product["category"].lower(), (
                f'For product id {product["id"]}, Expected to have category "{category}" got {product["category"]}'
            )

        self.logger.info(
            msg=f"Successfully retrieved {len(products)} products with category '{category}'"
        )
