import pytest
from flask import Flask
from flask.testing import FlaskClient


@pytest.mark.usefixtures("client", "server_app")
class TestSingleThread:
    def test_server(self, client: FlaskClient, server_app: Flask):
        response = client.get(f"/perfsim/")
        assert response.status_code == 200
        assert response.data.startswith(b"PerfSim v")
