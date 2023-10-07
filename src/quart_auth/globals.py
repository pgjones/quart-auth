from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator, Awaitable, Callable, Optional, TypeVar

from quart import current_app, Quart
from quart.typing import TestClientProtocol
from werkzeug.local import LocalProxy

from .extension import Action, AuthUser, QuartAuth, Unauthorized

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec  # type: ignore

T = TypeVar("T")
P = ParamSpec("P")


def _load_user() -> AuthUser:
    return _find_extension().load_user()


current_user: AuthUser = LocalProxy(_load_user)  # type: ignore


def _find_extension(app: Optional[Quart] = None) -> QuartAuth:
    if app is None:
        app = current_app
    extension = next(
        (extension for extension in app.extensions["QUART_AUTH"] if extension.singleton),
        None,
    )
    if extension is None:
        raise RuntimeError("No singleton QuartAuth, please see docs about multiple auth users")
    return extension


def login_required(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """A decorator to restrict route access to authenticated users.

    This should be used to wrap a route handler (or view function) to
    enforce that only authenticated requests can access it. Note that
    it is important that this decorator be wrapped by the route
    decorator and not vice, versa, as below.

    .. code-block:: python

        @app.route('/')
        @login_required
        async def index():
            ...

    If the request is not authenticated a
    `quart.exceptions.Unauthorized` exception will be raised.

    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not await current_user.is_authenticated:
            raise Unauthorized()
        else:
            return await current_app.ensure_async(func)(*args, **kwargs)

    return wrapper


def login_user(user: AuthUser, remember: bool = False) -> None:
    """Use this to start a session with the authenticated *user*.

    This will result in `current_user` resolving to the `user`.

    Arguments:
        user: The user to consider authenticated and to start a
            session for.
        remember: If True write consider the session permanent with
            a duration equal to the `QUART_AUTH_DURATION` configuration
            value.
    """
    if remember:
        user.action = Action.WRITE_PERMANENT
    else:
        user.action = Action.WRITE
    _find_extension().login_user(user)


def logout_user() -> None:
    """Use this to end the session of the current_user."""
    _find_extension().logout_user()


def renew_login() -> None:
    """Use this to renew the cookie (a new max age)."""
    current_user.action = Action.WRITE_PERMANENT


@asynccontextmanager
async def authenticated_client(
    client: TestClientProtocol, auth_id: str
) -> AsyncGenerator[None, None]:
    async with _find_extension(client.app).authenticated_client(client, auth_id) as auth_client:
        yield auth_client


def generate_auth_token(client: TestClientProtocol, auth_id: str) -> str:
    return _find_extension(client.app).dump_token(auth_id, app=client.app)
