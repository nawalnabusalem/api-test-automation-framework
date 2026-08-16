import pytest

from api.product.product_api import ProductAPI
from tests.base_test import BaseTest
from utils import HTTPStatus


class TestPutProductAPI(BaseTest):
    @pytest.fixture
    def product_api(self) -> ProductAPI:
        """Return an initialized Product API client."""
        return ProductAPI(self.api_client)

    @pytest.mark.parametrize(
        "product_id, new_title, new_price, new_description, new_category",
        [(1, "New Mascara Lash Princess", 16.0, "Automation put test product", "beauty")],
    )
    def test_put_existing_product_returns_updated_fields(
        self,
        product_id: int,
        new_title: str,
        new_price: float,
        new_description: str,
        new_category: str,
        product_api: ProductAPI,
    ) -> None:
        """Verify that Putting an existing product replaces the product."""
        self.logger.info(
            f"Replacing an existing product with product_id={product_id}, with new fields -- "
            f"title: {new_title}, price: {new_price}, description: {new_description}, category: {new_category}"
        )

        new_product = {
            "title": new_title,
            "price": new_price,
            "description": new_description,
            "category": new_category,
        }

        response = product_api.replace_product(product_id=product_id, product=new_product)

        assert response.status_code == HTTPStatus.OK.value, (
            f"Expected status code {HTTPStatus.OK.value}, got {response.status_code}"
        )

        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected Content Type JSON"
        )

        replaced_product = response.json()

        for field in ("id", "title", "price", "description", "category"):
            assert field in replaced_product, f"Expected '{field}' in product response"

        assert replaced_product["id"] == product_id, (
            f"Expected to get product id '{product_id}', got '{replaced_product['id']}'"
        )

        assert replaced_product["title"] == new_title, (
            f"Expected to update product title '{new_title}', got '{replaced_product['title']}'"
        )

        assert replaced_product["price"] == new_price, (
            f"Expected to update product price = {new_price}, got {replaced_product['price']}"
        )

        assert replaced_product["category"] == new_category, (
            f"Expected to update product category = {new_category}, got {replaced_product['category']}"
        )

        assert replaced_product["description"] == new_description, (
            f"Expected to update product description = {new_description}, got {replaced_product['description']}"
        )

        self.logger.info(msg="Successfully updated the product using PUT")
