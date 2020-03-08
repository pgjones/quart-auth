from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import auto, Enum
from functools import wraps
from typing import Any, Callable, Optional

from itsdangerous import BadSignature, URLSafeSerializer
from quart import current_app, has_request_context, Quart, request, Response
from quart.exceptions import Unauthorized
from quart.globals import _request_ctx_stack
from quart.local import LocalProxy

QUART_AUTH_USER_ATTRIBUTE = "_quart_auth_user"
DEFAULTS = {
    "QUART_AUTH_COOKIE_DOMAIN": None,
    "QUART_AUTH_COOKIE_NAME": "QUART_AUTH",
    "QUART_AUTH_COOKIE_PATH": "/",
    "QUART_AUTH_COOKIE_HTTP_ONLY": True,
    "QUART_AUTH_COOKIE_SAMESITE": "Strict",
    "QUART_AUTH_COOKIE_SECURE": True,
    "QUART_AUTH_DURATION": 365 * 24 * 60 * 60,  # 1 Year
    "QUART_AUTH_SALT": "quart auth salt",
}


current_user = LocalProxy(lambda: _load_user())


class Action(Enum):
    DELETE = auto()
    PASS = auto()
    WRITE = auto()
    WRITE_PERMANENT = auto()


class UserABC(ABC):
    """An abstract base class for users.

    Any specific user implementation used with Quart-Auth should
    inherit from this and implement the abstract methods.
    """

    action = Action.PASS

    @property
    @abstractmethod
    def auth_id(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    async def is_authenticated(self) -> bool:
        pass


class AnonymousUser(UserABC):
    @property
    def auth_id(self) -> Optional[str]:
        return None

    @property
    async def is_authenticated(self) -> bool:
        return False


class AuthenticatedUser(UserABC):
    def __init__(self, auth_id: str) -> None:
        self._auth_id = auth_id

    @property
    def auth_id(self) -> Optional[str]:
        return self._auth_id

    @property
    async def is_authenticated(self) -> bool:
        return True


class AuthManager:
    anonymous_user_class = AnonymousUser
    user_class = AuthenticatedUser

    def __init__(self, app: Optional[Quart] = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        app.auth_manager = self  # type: ignore
        app.after_request(self.after_request)

    def resolve_user(self) -> UserABC:
        auth_id = self.load_cookie()

        if auth_id is not None:
            return self.user_class(auth_id)
        else:
            return self.anonymous_user_class()

    def load_cookie(self) -> Optional[str]:
        try:
            token = request.cookies[_get_config_or_default("QUART_AUTH_COOKIE_NAME")]
        except KeyError:
            return None
        else:
            serializer = URLSafeSerializer(
                current_app.secret_key, _get_config_or_default("QUART_AUTH_SALT")
            )
            try:
                return serializer.loads(token)
            except BadSignature:
                return None

    def after_request(self, response: Response) -> Response:
        if current_user.action == Action.DELETE:
            response.delete_cookie(_get_config_or_default("QUART_AUTH_COOKIE_NAME"))
        elif current_user.action in {Action.WRITE, Action.WRITE_PERMANENT}:
            expires = None
            if current_user.action == Action.WRITE_PERMANENT:
                expires = datetime.utcnow() + timedelta(
                    seconds=_get_config_or_default("QUART_AUTH_DURATION")
                )

            serializer = URLSafeSerializer(
                current_app.secret_key, _get_config_or_default("QUART_AUTH_SALT")
            )
            token = serializer.dumps(current_user.auth_id)
            response.set_cookie(
                _get_config_or_default("QUART_AUTH_COOKIE_NAME"),
                token,
                domain=_get_config_or_default("QUART_AUTH_COOKIE_DOMAIN"),
                expires=expires,
                httponly=_get_config_or_default("QUART_AUTH_COOKIE_HTTP_ONLY"),
                path=_get_config_or_default("QUART_AUTH_COOKIE_PATH"),
                secure=_get_config_or_default("QUART_AUTH_COOKIE_SECURE"),
                samesite=_get_config_or_default("QUART_AUTH_COOKIE_SAMESITE"),
            )
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
            return await func(*args, **kwargs)

    return wrapper


def login_user(user: AuthenticatedUser, remember: bool = False) -> None:
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
    setattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE, user)


def logout_user() -> None:
    """Use this to end the session of the current_user."""
    current_user.action = Action.DELETE  # type: ignore


def _load_user() -> Optional[UserABC]:
    if has_request_context() and not hasattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE):
        user = current_app.auth_manager.resolve_user()
        setattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE, user)

    return getattr(
        _request_ctx_stack.top,
        QUART_AUTH_USER_ATTRIBUTE,
        current_app.auth_manager.anonymous_user_class(),
    )


def _get_config_or_default(config_key: str) -> Any:
    return current_app.config.get(config_key, DEFAULTS[config_key])
