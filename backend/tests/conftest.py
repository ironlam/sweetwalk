import pytest
from fastapi.testclient import TestClient

from sweetwalk.main import app


@pytest.fixture
def client():
    return TestClient(app)
