from functools import wraps
from secrets import compare_digest
from typing import Awaitable, Callable, TypeVar

from quart import current_app, has_request_context, has_websocket_context, request, websocket
from werkzeug.datastructures import WWWAuthenticate
from werkzeug.exceptions import Unauthorized as WerkzeugUnauthorized

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec  # type: ignore

T = TypeVar("T")
P = ParamSpec("P")


class UnauthorizedBasicAuth(WerkzeugUnauthorized):
    def __init__(self) -> None:
        www_authenticate = WWWAuthenticate("basic")
        super().__init__(www_authenticate=www_authenticate)


def basic_auth_required(
    username_key: str = "QUART_AUTH_BASIC_USERNAME",
    password_key: str = "QUART_AUTH_BASIC_PASSWORD",
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """A decorator to restrict route access to basic authenticated users.

    This should be used to wrap a route handler (or view function) to
    enforce that only basic authenticated requests can access it. The
    basic auth username and password are configurable via the app
    configuration with the QUART_AUTH_BASIC_USERNAME, and
    QUART_AUTH_BASIC_PASSWORD keys used by default. Note that it is
    important that this decorator be wrapped by the route decorator
    and not vice, versa, as below.

    .. code-block:: python

        @app.route('/')
        @basic_auth_required()
        async def index():
            ...

    If the request is not authenticated a
    `quart.exceptions.UnauthorizedBasicAuth` exception will be raised.

    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if has_request_context():
                auth = request.authorization
            elif has_websocket_context():
                auth = websocket.authorization
            else:
                raise RuntimeError("Not used in a valid request/websocket context")

            if (
                auth is not None
                and auth.type == "basic"
                and auth.username == current_app.config[username_key]
                and compare_digest(auth.password, current_app.config[password_key])
            ):
                return await current_app.ensure_async(func)(*args, **kwargs)
            else:
                raise UnauthorizedBasicAuth()

        return wrapper

    return decorator
