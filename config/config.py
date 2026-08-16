import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    USERNAME = os.getenv("TEST_USERNAME", "")
    PASSWORD = os.getenv("TEST_PASSWORD", "")
