from enum import StrEnum


class APISuite(StrEnum):
    """Canonical suite names used to group tests in the HTML report."""

    USER = "UserAPI"
    PRODUCT = "ProductAPI"
    AUTH = "AuthAPI"
