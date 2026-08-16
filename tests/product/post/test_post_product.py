import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestPostProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize(
        "product_title, product_price, description, category",
        [("New Mascara Lash Princess", 15.0, "Automation test product", "beauty")],
    )
    def test_post_a_new_product_returns_id(
        self,
        product_title: str,
        product_price: float,
        description: str,
        category: str,
        product_api: ProductAPI,
    ) -> None:
        """Verify that Posting a new product creates a new product."""
        self.logger.info(
            f"Creating a new product with product title: {product_title}, price: {product_price}, description: {description}, category: {category}"
        )

        new_product = {
            "title": product_title,
            "price": product_price,
            "description": description,
            "category": category,
        }

        response = product_api.create_a_new_product(product=new_product)

        assert response.status_code == HTTPStatus.CREATED.value, (
            f"Expected status code {HTTPStatus.CREATED.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        created_product = response.json()

        for field in ("id", "title", "price", "description", "category"):
            assert field in created_product, f"Expected '{field}' in product response"

        assert isinstance(created_product["id"], int), (
            f"Expected to get an integer product ID, got {type(created_product['id'])}"
        )

        assert created_product["title"] == product_title, (
            f"Expected to get product title '{product_title}', got '{created_product['title']}'"
        )

        assert created_product["price"] == product_price, (
            f"Expected to get product price = {product_price}, got {created_product['price']}"
        )

        self.logger.info("Successfully created a new product")
