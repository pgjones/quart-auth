from datetime import datetime, timedelta
from enum import auto, Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

from itsdangerous import BadSignature, URLSafeSerializer
from quart import current_app, has_request_context, Quart, request, Response
from quart.exceptions import Unauthorized as QuartUnauthorized
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


class Unauthorized(QuartUnauthorized):
    pass


class Action(Enum):
    DELETE = auto()
    PASS = auto()
    WRITE = auto()
    WRITE_PERMANENT = auto()


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
        app.context_processor(_template_context)

    def resolve_user(self) -> AuthUser:
        auth_id = self.load_cookie()

        return self.user_class(auth_id)

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
            response.delete_cookie(
                _get_config_or_default("QUART_AUTH_COOKIE_NAME"),
                domain=_get_config_or_default("QUART_AUTH_COOKIE_DOMAIN"),
            )
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
    setattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE, user)


def logout_user() -> None:
    """Use this to end the session of the current_user."""
    user = current_app.auth_manager.user_class(None)
    user.action = Action.DELETE
    setattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE, user)


def _load_user() -> AuthUser:
    if has_request_context() and not hasattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE):
        user = current_app.auth_manager.resolve_user()
        setattr(_request_ctx_stack.top, QUART_AUTH_USER_ATTRIBUTE, user)

    return getattr(
        _request_ctx_stack.top,
        QUART_AUTH_USER_ATTRIBUTE,
        current_app.auth_manager.user_class(None),
    )


def _get_config_or_default(config_key: str) -> Any:
    return current_app.config.get(config_key, DEFAULTS[config_key])


def _template_context() -> Dict[str, AuthUser]:
    return {"current_user": _load_user()}
