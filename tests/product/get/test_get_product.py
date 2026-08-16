import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestGetProductAPI(BaseTest):
    """Test suite for Product API GET endpoint."""

    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    def test_get_all_products_returns_non_empty_list(
        self,
        product_api: ProductAPI,
    ) -> None:
        """Verify that the Get All Products endpoint returns a successful response with at least one product."""

        self.logger.info(msg="Sending request to retrieve all products.")

        response = product_api.get_all_products()

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        response_data = response.json()
        products = response_data.get("products", [])

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )
        assert "products" in response_data, "Expected to get products JSON list"
        assert products, "Expected at least one product."
        assert "total" in response_data and response_data["total"] > 0, (
            f"Expected to get a positive total products, got {response_data.get('total')}"
        )
        assert len(products) <= response_data["limit"], (
            f"Expected to get products less than {response_data['limit']},Actual products length= {len(products)}, limit = {response_data['limit']}"
        )

        self.logger.info(msg=f"Retrieved {len(products)} products.")
        self.logger.info(msg=f"First product: Title={products[0].get('title')}")

    @pytest.mark.parametrize("product_id", [1, 2])
    def test_get_product_by_id_returns_expected_product(
        self,
        product_api: ProductAPI,
        product_id: int,
    ) -> None:
        """Verify that retrieving a product by ID returns the expected product."""
        self.logger.info(msg=f"Retrieving product with ID={product_id}")
        response = product_api.get_product_by_id(product_id=product_id)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        product = response.json()

        assert product, "Expected a product in the response."

        for field in ("id", "title", "price", "stock"):
            assert field in product, f"Expected '{field}' in product response"

        assert product["id"] == product_id, (
            f"Expected product ID {product_id}, got {product['id']}"
        )

        assert isinstance(product["title"], str) and product["title"].strip(), (
            "Expected non empty string product title"
        )

        assert isinstance(product["price"], (int, float)), (
            f"Expected to have a numeric product price, got {type(product['price'])}"
        )

        assert isinstance(product["stock"], int) and product["stock"] >= 0, (
            f"Expected non-negative integer stock, got {product['stock']}"
        )

        self.logger.info(
            msg=f"Successfully retrieved product: ID={product['id']}, Title={product['title']}"
        )

    @pytest.mark.parametrize("product_id", [9999, 0, -3])
    def test_get_product_by_invalid_id_returns_not_found(
        self,
        product_id: int,
        product_api: ProductAPI,
    ) -> None:
        """Verify that requesting a non-existent product ID returns a 404 response with an appropriate error message."""

        self.logger.info(f"Retrieving product with invalid ID={product_id}")

        response = product_api.get_product_by_id(product_id=product_id)

        assert response.status_code == HTTPStatus.NOT_FOUND.value, (
            f"Expected status code {HTTPStatus.NOT_FOUND.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        error = response.json()

        message = error["message"].lower()
        assert "not found" in message, "Expected a non-empty error message."

        self.logger.info(
            msg=f"Received expected error for product ID={product_id}: {error['message']}"
        )
