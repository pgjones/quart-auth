import warnings
from contextlib import asynccontextmanager
from enum import auto, Enum
from hashlib import sha512
from typing import Any, AsyncGenerator, cast, Dict, Literal, Optional, Type, Union

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
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
from werkzeug.exceptions import Unauthorized as WerkzeugUnauthorized

DEFAULTS = {
    "QUART_AUTH_ATTRIBUTE_NAME": "_quart_auth_user",
    "QUART_AUTH_BASIC_USERNAME": None,
    "QUART_AUTH_BASIC_PASSWORD": None,
    "QUART_AUTH_COOKIE_DOMAIN": None,
    "QUART_AUTH_COOKIE_NAME": "QUART_AUTH",
    "QUART_AUTH_COOKIE_PATH": "/",
    "QUART_AUTH_COOKIE_HTTP_ONLY": True,
    "QUART_AUTH_COOKIE_SAMESITE": "Lax",
    "QUART_AUTH_COOKIE_SECURE": True,
    "QUART_AUTH_DURATION": 365 * 24 * 60 * 60,  # 1 Year
    "QUART_AUTH_MODE": "cookie",  # "bearer" | "cookie"
    "QUART_AUTH_SALT": "quart auth salt",
}


class Unauthorized(WerkzeugUnauthorized):
    pass


class Action(Enum):
    DELETE = auto()
    PASS = auto()
    WRITE = auto()
    WRITE_PERMANENT = auto()


class _AuthSerializer(URLSafeTimedSerializer):
    def __init__(self, secret: Union[str, bytes], salt: Union[str, bytes]) -> None:
        super().__init__(secret, salt, signer_kwargs={"digest_method": sha512})


class AuthUser:
    """A base class for users.

    Any specific user implementation used with Quart-Auth should
    inherit from this.
    """

    def __init__(self, auth_id: Optional[str], action: Action = Action.PASS) -> None:
        self._auth_id = auth_id
        self.action = action

    @property
    def auth_id(self) -> Optional[str]:
        return self._auth_id

    @property
    async def is_authenticated(self) -> bool:
        return self._auth_id is not None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(auth_id={self._auth_id}, action={self.action})"


class QuartAuth:
    user_class = AuthUser
    serializer_class = _AuthSerializer

    def __init__(
        self,
        app: Optional[Quart] = None,
        *,
        attribute_name: str = None,
        cookie_domain: Optional[str] = None,
        cookie_name: Optional[str] = None,
        cookie_path: Optional[str] = None,
        cookie_http_only: Optional[bool] = None,
        cookie_samesite: Optional[Literal["Strict", "Lax"]] = None,
        cookie_secure: Optional[bool] = None,
        duration: Optional[int] = None,
        mode: Optional[Literal["cookie", "bearer"]] = None,
        salt: Optional[str] = None,
        singleton: bool = True,
        serializer_class: Optional[Type[_AuthSerializer]] = None,
        user_class: Optional[Type[AuthUser]] = None,
    ) -> None:
        self.attribute_name = attribute_name
        self.cookie_domain = cookie_domain
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_http_only = cookie_http_only
        self.cookie_samesite = cookie_samesite
        self.cookie_secure = cookie_secure
        self.duration = duration
        self.mode = mode
        self.salt = salt
        self.singleton = singleton
        if serializer_class is not None:
            self.serializer_class = serializer_class
        if serializer_class is not None:
            self.user_class = user_class
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        if self.attribute_name is None:
            self.attribute_name = _get_config_or_default("QUART_AUTH_ATTRIBUTE_NAME", app)
        if self.cookie_domain is None:
            self.cookie_domain = _get_config_or_default("QUART_AUTH_COOKIE_DOMAIN", app)
        if self.cookie_name is None:
            self.cookie_name = _get_config_or_default("QUART_AUTH_COOKIE_NAME", app)
        if self.cookie_path is None:
            self.cookie_path = _get_config_or_default("QUART_AUTH_COOKIE_PATH", app)
        if self.cookie_http_only is None:
            self.cookie_http_only = _get_config_or_default("QUART_AUTH_COOKIE_HTTP_ONLY", app)
        if self.cookie_samesite is None:
            self.cookie_samesite = _get_config_or_default("QUART_AUTH_COOKIE_SAMESITE", app)
        if self.cookie_secure is None:
            self.cookie_secure = _get_config_or_default("QUART_AUTH_COOKIE_SECURE", app)
        if self.duration is None:
            self.duration = _get_config_or_default("QUART_AUTH_DURATION", app)
        if self.mode is None:
            self.mode = _get_config_or_default("QUART_AUTH_MODE", app)
        if self.salt is None:
            self.salt = _get_config_or_default("QUART_AUTH_SALT", app)

        if any(
            ext.attribute_name == self.attribute_name
            or ext.cookie_name == self.cookie_name
            or ext.salt == self.salt
            for ext in app.extensions.get("QUART_AUTH", [])
        ):
            warnings.warn(
                "The same attribute name/cookie name/salt is used by another QuartAuth "
                "instance, this may result in insecure usage."
            )

        app.extensions.setdefault("QUART_AUTH", []).append(self)

        if sum(ext.singleton for ext in app.extensions["QUART_AUTH"]) > 2:
            raise RuntimeError(
                "Multiple singleton extensions, please see docs about multiple auth users"
            )

        app.after_request(self.after_request)
        app.after_websocket(self.after_websocket)  # type: ignore
        if self.singleton:
            app.context_processor(self._template_context)

    def resolve_user(self) -> AuthUser:
        if self.mode == "cookie":
            auth_id = self.load_cookie()
        else:
            auth_id = self.load_bearer()

        return self.user_class(auth_id)

    def load_cookie(self) -> Optional[str]:
        try:
            token = ""
            if has_request_context():
                token = request.cookies[self.cookie_name]
            elif has_websocket_context():
                token = websocket.cookies[self.cookie_name]
        except KeyError:
            return None
        else:
            return self.load_token(token)

    def load_bearer(self) -> Optional[str]:
        try:
            if has_request_context():
                raw = request.headers["Authorization"]
            elif has_websocket_context():
                raw = websocket.headers["Authorization"]
        except KeyError:
            return None
        else:
            if raw[:6].lower() != "bearer":
                return None
            token = raw[6:].strip()
            return self.load_token(token)

    def dump_token(self, auth_id: str, app: Optional[Quart] = None) -> str:
        if app is None:
            app = current_app

        serializer = self.serializer_class(app.secret_key, self.salt)
        return serializer.dumps(auth_id)

    def load_token(self, token: str, app: Optional[Quart] = None) -> Optional[str]:
        if app is None:
            app = current_app

        serializer = self.serializer_class(app.secret_key, self.salt)
        try:
            return serializer.loads(token, max_age=self.duration)
        except (BadSignature, SignatureExpired):
            return None

    async def after_request(self, response: Response) -> Response:
        user = self.load_user()
        if self.mode == "bearer":
            if user.action != Action.PASS:
                warnings.warn("Login/logout/renew have no affect in bearer mode")

            return response

        if user.action == Action.DELETE:
            response.delete_cookie(
                self.cookie_name,
                domain=self.cookie_domain,
                httponly=cast(bool, self.cookie_http_only),
                path=self.cookie_path,
                secure=cast(bool, self.cookie_secure),
                samesite=self.cookie_samesite,
            )
        elif user.action in {Action.WRITE, Action.WRITE_PERMANENT}:
            max_age = None
            if user.action == Action.WRITE_PERMANENT:
                max_age = self.duration

            if self.cookie_secure and not request.is_secure:
                warnings.warn("Secure cookies will be ignored on insecure requests")

            if self.cookie_samesite == "Strict" and 300 <= response.status_code < 400:
                warnings.warn("Strict samesite cookies will be ignored on redirects")

            token = self.dump_token(user.auth_id)
            response.set_cookie(
                self.cookie_name,
                token,
                domain=self.cookie_domain,
                max_age=max_age,
                httponly=cast(bool, self.cookie_http_only),
                path=self.cookie_path,
                secure=cast(bool, self.cookie_secure),
                samesite=self.cookie_samesite,
            )
        return response

    async def after_websocket(self, response: Optional[Response]) -> Optional[Response]:
        user = self.load_user()
        if self.mode == "bearer":
            if user.action != Action.PASS:
                warnings.warn("Login/logout/renew have no affect in bearer mode")

            return response

        if user.action != Action.PASS:
            if response is not None:
                warnings.warn(
                    "The auth cookie may not be set by the client. "
                    "Cookies are unreliably set on websocket responses."
                )
            else:
                warnings.warn("The auth cookie cannot be set by the client.")

        return response

    def load_user(self) -> AuthUser:
        if has_request_context():
            if not hasattr(request_ctx, self.attribute_name):
                user = self.resolve_user()
                setattr(request_ctx, self.attribute_name, user)

            return getattr(
                request_ctx,
                self.attribute_name,
                self.user_class(None),
            )
        elif has_websocket_context():
            if not hasattr(websocket_ctx, self.attribute_name):
                user = self.resolve_user()
                setattr(websocket_ctx, self.attribute_name, user)

            return getattr(
                websocket_ctx,
                self.attribute_name,
                self.user_class(None),
            )
        else:
            return self.user_class(None)

    def login_user(self, user: AuthUser) -> None:
        if has_request_context():
            setattr(request_ctx, self.attribute_name, user)
        else:
            raise RuntimeError("Cannot login unless within a request context")

    def logout_user(self) -> None:
        user = self.user_class(None)
        user.action = Action.DELETE
        if has_request_context():
            setattr(request_ctx, self.attribute_name, user)
        else:
            raise RuntimeError("Cannot logout unless within a request context")

    @asynccontextmanager
    async def authenticated_client(
        self, client: TestClientProtocol, auth_id: str
    ) -> AsyncGenerator[None, None]:
        if client.cookie_jar is None or self.mode != "cookie":
            raise RuntimeError("Authenticated transactions only make sense with cookies enabled.")

        token = self.dump_token(auth_id, app=client.app)
        client.set_cookie(
            self.cookie_domain,
            self.cookie_name,
            token,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=cast(bool, self.cookie_secure),
            httponly=cast(bool, self.cookie_http_only),
            samesite=self.cookie_samesite,
        )
        yield
        client.delete_cookie(
            self.cookie_domain,
            self.cookie_name,
            path=self.cookie_path,
            domain=self.cookie_domain,
        )

    def _template_context(self) -> Dict[str, AuthUser]:
        return {"current_user": self.load_user()}


def _get_config_or_default(config_key: str, app: Quart) -> Any:
    return app.config.get(config_key, DEFAULTS[config_key])
