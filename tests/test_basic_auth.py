import pytest
from quart import Quart, ResponseReturnValue, websocket
from werkzeug.datastructures import Authorization

from quart_auth import AuthManager, basic_auth_required


@pytest.fixture(name="app")
def _app() -> Quart:
    app = Quart(__name__)
    app.config["QUART_AUTH_BASIC_USERNAME"] = "test"
    app.config["QUART_AUTH_BASIC_PASSWORD"] = "test"
    app.secret_key = "Secret"

    @app.route("/")
    async def index() -> ResponseReturnValue:
        return "index"

    @app.route("/basic")
    @basic_auth_required()
    async def basic_auth() -> ResponseReturnValue:
        return "Basic"

    @app.websocket("/ws")
    @basic_auth_required()
    async def ws() -> None:
        data = await websocket.receive()
        await websocket.send(data)

    AuthManager(app)
    return app


@pytest.mark.asyncio
async def test_no_auth(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_basic_auth(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/basic")
    assert response.status_code == 401
    auth = Authorization("basic", {"username": "test", "password": "test"})
    response = await test_client.get("/basic", headers={"Authorization": auth.to_header()})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_websocket_basic_auth(app: Quart) -> None:
    test_client = app.test_client()
    await test_client.get("/login")
    auth = Authorization("basic", {"username": "test", "password": "test"})
    async with test_client.websocket("/ws", headers={"Authorization": auth.to_header()}) as ws:
        await ws.send("Hello")
        assert (await ws.receive()) == "Hello"
