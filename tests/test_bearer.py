import pytest
from quart import Quart, render_template_string, ResponseReturnValue, websocket
from werkzeug.datastructures import Headers

from quart_auth import AuthManager, current_user, login_required


@pytest.fixture(name="app")
def _app() -> Quart:
    app = Quart(__name__)
    app.config["QUART_AUTH_MODE"] = "bearer"
    app.secret_key = "Secret"
    auth_manager = AuthManager(app)

    @app.route("/")
    async def index() -> ResponseReturnValue:
        return "index"

    @app.route("/auth")
    @login_required
    async def auth() -> ResponseReturnValue:
        return "auth"

    @app.route("/templating")
    @login_required
    async def templating() -> ResponseReturnValue:
        return await render_template_string("Hello {{ current_user.auth_id }}")

    @app.route("/login")
    async def login() -> ResponseReturnValue:
        token = auth_manager.dump_token("2")
        return {"token": token}

    @app.websocket("/ws")
    @login_required
    async def ws() -> None:
        data = await websocket.receive()
        await websocket.send(f"{data} {current_user.auth_id}")

    return app


@pytest.mark.asyncio
async def test_no_auth(app: Quart) -> None:
    async with app.test_request_context("/"):
        assert not (await current_user.is_authenticated)
        assert current_user.auth_id is None


@pytest.mark.asyncio
async def test_auth(app: Quart) -> None:
    test_client = app.test_client()
    token = test_client.generate_auth_token("1")  # type: ignore
    headers = Headers()
    headers.add("Authorization", f"bearer {token}")
    async with app.test_request_context("/", headers=headers):
        assert await current_user.is_authenticated
        assert current_user.auth_id == "1"


@pytest.mark.asyncio
async def test_templating(app: Quart) -> None:
    test_client = app.test_client()
    token = test_client.generate_auth_token("1")  # type: ignore
    response = await test_client.get("/templating", headers={"Authorization": f"bearer {token}"})
    assert (await response.get_data()) == b"Hello 1"  # type: ignore


@pytest.mark.asyncio
async def test_login_required(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/auth")
    assert response.status_code == 401

    token = test_client.generate_auth_token("1")  # type: ignore
    response = await test_client.get("/auth", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/login")
    assert response.status_code == 200
    assert "token" in (await response.get_json())


@pytest.mark.asyncio
async def test_websocket(app: Quart) -> None:
    test_client = app.test_client()
    token = test_client.generate_auth_token("1")  # type: ignore
    async with test_client.websocket("/ws", headers={"Authorization": f"bearer {token}"}) as ws:
        await ws.send("Hello")
        assert (await ws.receive()) == "Hello 1"
