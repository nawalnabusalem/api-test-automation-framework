import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestSearchProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize("search_query", ["phone"])
    def test_search_product_by_query_returns_expected_product_list(
        self,
        product_api: ProductAPI,
        search_query: str,
    ) -> None:
        """Verify that retrieving products by query returns the expected products list."""
        self.logger.info(msg=f"Searching for products with query '{search_query}'")

        response = product_api.search_product_by_query(search_query=search_query)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        response_data = response.json()

        assert "products" in response_data, 'Expected field "products" not found in response'

        products = response_data.get("products", [])

        assert len(products) > 0, (
            f'Expected to have at least 1 product matching query "{search_query}"'
        )

        for product in products:
            searchable_text = " ".join(
                [
                    str(product.get("title", "")),
                    str(product.get("description", "")),
                    str(product.get("category", "")),
                    str(product.get("brand", "")),
                    " ".join(product.get("tags", [])),
                ]
            )
            assert search_query.lower() in searchable_text.lower(), (
                f"Product ID {product.get('id')} did not match query {search_query}"
            )

        self.logger.info(
            msg=f"Successfully retrieved {len(products)} products with search query '{search_query}'"
        )
