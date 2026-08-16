from api.api_client import APIClient


class AuthAPI:
    def __init__(self, client: APIClient):
        self.client = client
        self.endpoint = "auth"

    def login_with_credentials(self, credentials: dict[str, str]):
        return self.client.post(
            endpoint=f"{self.endpoint}/login",
            payload=credentials,
            show_headers=False,
            show_body=True,
        )

    def get_authenticated_user_profile(self):
        return self.client.get(
            endpoint=f"{self.endpoint}/me", show_headers=False, show_body=False
        )
