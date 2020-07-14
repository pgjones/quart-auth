import pytest
from quart import Quart, redirect, render_template_string, ResponseReturnValue, url_for
from werkzeug.datastructures import Headers

from quart_auth import (
    _AuthSerializer,
    AuthManager,
    AuthUser,
    current_user,
    DEFAULTS,
    login_required,
    login_user,
    logout_user,
    Unauthorized,
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

    @app.route("/templating")
    @login_required
    async def templating() -> ResponseReturnValue:
        return await render_template_string("Hello {{ current_user.auth_id }}")

    @app.route("/login")
    async def login() -> ResponseReturnValue:
        login_user(AuthUser("2"))
        return "login"

    @app.route("/logout")
    async def logout() -> ResponseReturnValue:
        logout_user()
        return "logout"

    @app.errorhandler(Unauthorized)
    async def redirect_to_login(*_: Exception) -> ResponseReturnValue:
        return redirect(url_for("login"))

    AuthManager(app)
    return app


@pytest.mark.asyncio
async def test_no_auth(app: Quart) -> None:
    async with app.test_request_context("/"):
        assert not (await current_user.is_authenticated)
        assert current_user.auth_id is None


@pytest.mark.asyncio
async def test_auth(app: Quart) -> None:
    serializer = _AuthSerializer(app.secret_key, DEFAULTS["QUART_AUTH_SALT"])  # type: ignore
    token = serializer.dumps("1")
    headers = Headers()
    headers.add("cookie", f"{DEFAULTS['QUART_AUTH_COOKIE_NAME']}={token}")
    async with app.test_request_context("/", headers=headers):
        assert await current_user.is_authenticated
        assert current_user.auth_id == "1"


@pytest.mark.asyncio
async def test_templating(app: Quart) -> None:
    test_client = app.test_client()
    await test_client.get("/login")
    response = await test_client.get("/templating")
    assert (await response.get_data()) == b"Hello 2"  # type: ignore


@pytest.mark.asyncio
async def test_login_required(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/auth")
    assert response.status_code == 302

    serializer = _AuthSerializer(app.secret_key, DEFAULTS["QUART_AUTH_SALT"])  # type: ignore
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
    assert response.status_code == 302


@pytest.mark.asyncio
async def test_redirect(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/auth")
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_login_cookie(app: Quart) -> None:
    test_client = app.test_client()
    await test_client.get("/login")
    assert next(cookie for cookie in test_client.cookie_jar).name == "QUART_AUTH"
