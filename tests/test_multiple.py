from functools import wraps
from typing import Any

import pytest
from quart import current_app, Quart, ResponseReturnValue
from werkzeug.local import LocalProxy

from quart_auth import Action, AuthUser, QuartAuth, Unauthorized


@pytest.fixture(name="app")
def _app() -> Quart:
    app = Quart(__name__)
    app.secret_key = "Secret"

    staff_auth = QuartAuth(
        app, attribute_name="staff", cookie_name="STAFF", salt="staff salt", singleton=False
    )
    admin_auth = QuartAuth(
        app, attribute_name="admin", cookie_name="ADMIN", salt="admin salt", singleton=False
    )

    current_staff = LocalProxy(lambda: staff_auth.load_user())

    def staff_login_required(func: Any) -> Any:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not await current_staff.is_authenticated:  # type: ignore
                raise Unauthorized()
            else:
                return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    current_admin = LocalProxy(lambda: admin_auth.load_user())

    def admin_login_required(func: Any) -> Any:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not await current_admin.is_authenticated:  # type: ignore
                raise Unauthorized()
            else:
                return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    @app.post("/staff-login")
    async def staff_login() -> ResponseReturnValue:
        staff_auth.login_user(AuthUser("2", Action.WRITE))
        return ""

    @app.get("/staff")
    @staff_login_required
    async def staff() -> ResponseReturnValue:
        return "staff"

    @app.post("/admin-login")
    async def admin_login() -> ResponseReturnValue:
        admin_auth.login_user(AuthUser("2", Action.WRITE))
        return ""

    @app.get("/admin")
    @admin_login_required
    async def admin() -> ResponseReturnValue:
        return "admin"

    return app


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["admin", "staff"])
async def test_login_required(mode: str, app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/admin")
    assert response.status_code == 401
    response = await test_client.get("/staff")
    assert response.status_code == 401

    await test_client.post(f"/{mode}-login")
    response = await test_client.get(f"/{mode}")
    assert response.status_code == 200
    response = await test_client.get("/admin" if mode == "staff" else "/staff")
    assert response.status_code == 401
