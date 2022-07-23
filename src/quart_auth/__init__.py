import warnings
from contextlib import asynccontextmanager
from enum import auto, Enum
from functools import wraps
from hashlib import sha512
from secrets import compare_digest
from types import new_class
from typing import Any, AsyncGenerator, Callable, Dict, Optional

from itsdangerous import BadSignature, URLSafeSerializer
from quart import (
    current_app,
    has_request_context,
    has_websocket_context,
    Quart,
    request,
    Response,
    websocket,
)
from quart.globals import request_ctx, websocket_ctx
from quart.typing import TestClientProtocol
from werkzeug.datastructures import WWWAuthenticate
from werkzeug.exceptions import Unauthorized as WerkzeugUnauthorized
from werkzeug.local import LocalProxy

QUART_AUTH_USER_ATTRIBUTE = "_quart_auth_user"
DEFAULTS = {
    "QUART_AUTH_BASIC_USERNAME": None,
    "QUART_AUTH_BASIC_PASSWORD": None,
    "QUART_AUTH_COOKIE_DOMAIN": None,
    "QUART_AUTH_COOKIE_NAME": "QUART_AUTH",
    "QUART_AUTH_COOKIE_PATH": "/",
    "QUART_AUTH_COOKIE_HTTP_ONLY": True,
    "QUART_AUTH_COOKIE_SAMESITE": "Lax",
    "QUART_AUTH_COOKIE_SECURE": True,
    "QUART_AUTH_DURATION": 365 * 24 * 60 * 60,  # 1 Year
    "QUART_AUTH_SALT": "quart auth salt",
}


current_user: "AuthUser" = LocalProxy(lambda: _load_user())  # type: ignore


class Unauthorized(WerkzeugUnauthorized):
    pass


class UnauthorizedBasicAuth(WerkzeugUnauthorized):
    def __init__(self) -> None:
        www_authenticate = WWWAuthenticate()
        www_authenticate.set_basic()
        super().__init__(www_authenticate=www_authenticate)


class Action(Enum):
    DELETE = auto()
    PASS = auto()
    WRITE = auto()
    WRITE_PERMANENT = auto()


class _AuthSerializer(URLSafeSerializer):
    def __init__(self, secret: str, salt: str) -> None:
        super().__init__(secret, salt, signer_kwargs={"digest_method": sha512})


class TestClientMixin:
    @asynccontextmanager
    async def authenticated(self: TestClientProtocol, auth_id: str) -> AsyncGenerator[None, None]:
        if self.cookie_jar is None:
            raise RuntimeError("Authenticated transactions only make sense with cookies enabled.")

        serializer = _AuthSerializer(
            self.app.secret_key,
            _get_config_or_default("QUART_AUTH_SALT", self.app),
        )
        token = serializer.dumps(auth_id)
        self.set_cookie(
            _get_config_or_default("QUART_AUTH_COOKIE_DOMAIN", self.app),
            _get_config_or_default("QUART_AUTH_COOKIE_NAME", self.app),
            token,  # type: ignore
            path=_get_config_or_default("QUART_AUTH_COOKIE_PATH", self.app),
            domain=_get_config_or_default("QUART_AUTH_COOKIE_DOMAIN", self.app),
            secure=_get_config_or_default("QUART_AUTH_COOKIE_SECURE", self.app),
            httponly=_get_config_or_default("QUART_AUTH_COOKIE_HTTP_ONLY", self.app),
            samesite=_get_config_or_default("QUART_AUTH_COOKIE_SAMESITE", self.app),
        )
        yield
        self.delete_cookie(
            _get_config_or_default("QUART_AUTH_COOKIE_DOMAIN", self.app),
            _get_config_or_default("QUART_AUTH_COOKIE_NAME", self.app),
            path=_get_config_or_default("QUART_AUTH_COOKIE_PATH", self.app),
            domain=_get_config_or_default("QUART_AUTH_COOKIE_DOMAIN", self.app),
        )


class AuthUser:
    """A base class for users.

    Any specific user implementation used with Quart-Auth should
    inherit from this.
    """

    def __init__(self, auth_id: Optional[str]) -> None:
        self._auth_id = auth_id
        self.action = Action.PASS

    @property
    def auth_id(self) -> Optional[str]:
        return self._auth_id

    @property
    async def is_authenticated(self) -> bool:
        return self._auth_id is not None


class AuthManager:
    user_class = AuthUser

    def __init__(self, app: Optional[Quart] = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        app.auth_manager = self  # type: ignore
        app.after_request(self.after_request)
        app.after_websocket(self.after_websocket)
        app.context_processor(_template_context)
        app.test_client_class = new_class("TestClient", (TestClientMixin, app.test_client_class))

    def resolve_user(self) -> AuthUser:
        auth_id = self.load_cookie()

        return self.user_class(auth_id)

    def load_cookie(self) -> Optional[str]:
        try:
            token = ""
            if has_request_context():
                token = request.cookies[_get_config_or_default("QUART_AUTH_COOKIE_NAME")]
            elif has_websocket_context():
                token = websocket.cookies[_get_config_or_default("QUART_AUTH_COOKIE_NAME")]
        except KeyError:
            return None
        else:
            serializer = _AuthSerializer(
                current_app.secret_key,
                _get_config_or_default("QUART_AUTH_SALT"),
            )
            try:
                return serializer.loads(token)
            except BadSignature:
                return None

    def after_request(self, response: Response) -> Response:
        if current_user.action == Action.DELETE:
            response.delete_cookie(
                _get_config_or_default("QUART_AUTH_COOKIE_NAME"),
                domain=_get_config_or_default("QUART_AUTH_COOKIE_DOMAIN"),
                httponly=_get_config_or_default("QUART_AUTH_COOKIE_HTTP_ONLY"),
                path=_get_config_or_default("QUART_AUTH_COOKIE_PATH"),
                secure=_get_config_or_default("QUART_AUTH_COOKIE_SECURE"),
                samesite=_get_config_or_default("QUART_AUTH_COOKIE_SAMESITE"),
            )
        elif current_user.action in {Action.WRITE, Action.WRITE_PERMANENT}:
            max_age = None
            if current_user.action == Action.WRITE_PERMANENT:
                max_age = _get_config_or_default("QUART_AUTH_DURATION")

            serializer = _AuthSerializer(
                current_app.secret_key,
                _get_config_or_default("QUART_AUTH_SALT"),
            )
            token = serializer.dumps(current_user.auth_id)
            response.set_cookie(
                _get_config_or_default("QUART_AUTH_COOKIE_NAME"),
                token,  # type: ignore
                domain=_get_config_or_default("QUART_AUTH_COOKIE_DOMAIN"),
                max_age=max_age,
                httponly=_get_config_or_default("QUART_AUTH_COOKIE_HTTP_ONLY"),
                path=_get_config_or_default("QUART_AUTH_COOKIE_PATH"),
                secure=_get_config_or_default("QUART_AUTH_COOKIE_SECURE"),
                samesite=_get_config_or_default("QUART_AUTH_COOKIE_SAMESITE"),
            )
        return response

    def after_websocket(self, response: Optional[Response]) -> Optional[Response]:
        if current_user.action != Action.PASS:
            if response is not None:
                warnings.warn(
                    "The auth cookie may not be set by the client. "
                    "Cookies are unreliably set on websocket responses."
                )
            else:
                warnings.warn("The auth cookie cannot be set by the client.")

        return response


def login_required(func: Callable) -> Callable:
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
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    if has_request_context():
        setattr(request_ctx, QUART_AUTH_USER_ATTRIBUTE, user)
    else:
        raise RuntimeError("Cannot login unless within a request context")


def logout_user() -> None:
    """Use this to end the session of the current_user."""
    user = current_app.auth_manager.user_class(None)  # type: ignore
    user.action = Action.DELETE
    if has_request_context():
        setattr(request_ctx, QUART_AUTH_USER_ATTRIBUTE, user)
    else:
        raise RuntimeError("Cannot logout unless within a request context")


def renew_login() -> None:
    """Use this to renew the cookie (a new max age)."""
    current_user.action = Action.WRITE_PERMANENT


def basic_auth_required(
    username_key: str = "QUART_AUTH_BASIC_USERNAME",
    password_key: str = "QUART_AUTH_BASIC_PASSWORD",
) -> Callable:
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

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def _load_user() -> AuthUser:
    if has_request_context():
        if not hasattr(request_ctx, QUART_AUTH_USER_ATTRIBUTE):
            user = current_app.auth_manager.resolve_user()  # type: ignore
            setattr(request_ctx, QUART_AUTH_USER_ATTRIBUTE, user)

        return getattr(
            request_ctx,
            QUART_AUTH_USER_ATTRIBUTE,
            current_app.auth_manager.user_class(None),  # type: ignore
        )
    elif has_websocket_context():
        if not hasattr(websocket_ctx, QUART_AUTH_USER_ATTRIBUTE):
            user = current_app.auth_manager.resolve_user()  # type: ignore
            setattr(websocket_ctx, QUART_AUTH_USER_ATTRIBUTE, user)

        return getattr(
            websocket_ctx,
            QUART_AUTH_USER_ATTRIBUTE,
            current_app.auth_manager.user_class(None),  # type: ignore
        )
    else:
        return current_app.auth_manager.user_class(None)  # type: ignore


def _get_config_or_default(config_key: str, app: Optional[Quart] = None) -> Any:
    if app is None:
        app = current_app
    return app.config.get(config_key, DEFAULTS[config_key])


def _template_context() -> Dict[str, AuthUser]:
    return {"current_user": _load_user()}
