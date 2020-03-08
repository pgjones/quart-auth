import pytest
from itsdangerous import URLSafeSerializer
from quart import Quart, ResponseReturnValue
from werkzeug.datastructures import Headers

from quart_auth import (
    AuthenticatedUser,
    AuthManager,
    current_user,
    DEFAULTS,
    login_required,
    login_user,
    logout_user,
)


@pytest.fixture(name="app")
def _app() -> Quart:
    app = Quart(__name__)
    app.secret_key = "Secret"

    @app.route("/")
    async def index() -> ResponseReturnValue:
        return "index"

    @app.route("/auth")
    @login_required
    async def auth() -> ResponseReturnValue:
        return "auth"

    @app.route("/login")
    async def login() -> ResponseReturnValue:
        login_user(AuthenticatedUser("2"))
        return "login"

    @app.route("/logout")
    async def logout() -> ResponseReturnValue:
        logout_user()
        return "logout"

    AuthManager(app)
    return app


@pytest.mark.asyncio
async def test_no_auth(app: Quart) -> None:
    async with app.test_request_context("/"):
        assert not (await current_user.is_authenticated)
        assert current_user.auth_id is None


@pytest.mark.asyncio
async def test_auth(app: Quart) -> None:
    serializer = URLSafeSerializer(app.secret_key, DEFAULTS["QUART_AUTH_SALT"])  # type: ignore
    token = serializer.dumps("1")
    headers = Headers()
    headers.add("cookie", f"{DEFAULTS['QUART_AUTH_COOKIE_NAME']}={token}")
    async with app.test_request_context("/", headers=headers):
        assert await current_user.is_authenticated
        assert current_user.auth_id == "1"


@pytest.mark.asyncio
async def test_login_required(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/auth")
    assert response.status_code == 401

    serializer = URLSafeSerializer(app.secret_key, DEFAULTS["QUART_AUTH_SALT"])  # type: ignore
    token = serializer.dumps(1)
    headers = Headers()
    headers.add("cookie", f"{DEFAULTS['QUART_AUTH_COOKIE_NAME']}={token}")

    response = await test_client.get("/auth", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_logout(app: Quart) -> None:
    test_client = app.test_client()
    await test_client.get("/login")
    response = await test_client.get("/auth")
    assert response.status_code == 200
    await test_client.get("/logout")
    response = await test_client.get("/auth")
    assert response.status_code == 401
