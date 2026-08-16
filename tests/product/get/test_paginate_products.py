import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestPaginateProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize("skip, limit", [(5, 5)])
    def test_paginate_product_returns_product_list(
        self, product_api: ProductAPI, skip: int, limit: int
    ) -> None:
        """Verify that Paginating product list returns a limited product list."""

        self.logger.info(
            msg=f"Paginating product list to get {limit} products, skipping the first {skip} products"
        )

        response = product_api.get_product_pagination_list(limit=limit, skip=skip)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        response_data = response.json()
        products = response_data.get("products", [])

        for field in ("products", "total", "skip", "limit"):
            assert field in response_data, f"Expected field {field} in response"

        assert response_data["total"] > 0, (
            f"Expected at least total = 1, got {response_data['total']}"
        )
        assert response_data["limit"] == limit, (
            f"Expected limit to be {limit}, got {response_data['limit']}"
        )
        assert response_data["skip"] == skip, (
            f"Expected skip to be {skip}, got {response_data['skip']}"
        )

        assert len(products) <= limit, f"Expected to get {limit} products, got {len(products)}"

        assert response_data["total"] >= skip + len(products), (
            f"Expected total at least equal skip + product list, got total {response_data['total']}"
        )

        self.logger.info(
            msg=f"Successfully paginated product list to get {limit} products, skipping the first {skip} products"
        )
