.. _token_generation:

Customising the token
=====================

The token used to authenticate requests is generated by Quart-Auth's
QuartAuth class and can be customised. The serializer class itself
is customisable and can be changed via the
``QuartAuth.serializer_class`` attribute. In addition the
serialization and deserialization methods can be changed to fully
customise the token usage.

For example to log when a user attempts to use an expired token the
following can be used:

.. code-block:: python

    import logging

    from itsdangerous import BadSignature, SignatureExpired
    from quart_auth import _get_config_or_default, QuartAuth

    log = logging.getLogger(__name__)

    class CustomQuartAuth(QuartAuth):
        def load_token(self, token: str, app: Optional[Quart] = None) -> Optional[str]:
            if app is None:
                app = current_app

            serializer = URLSafeTimedSerializer(
                app.secret_key,
                _get_config_or_default("QUART_AUTH_SALT", app),
            )
            try:
                return serializer.loads(
                    token,
                    max_age=_get_config_or_default("QUART_AUTH_DURATION", app)
                )
            except SignatureExpired:
                auth_id, _ = serializer.loads_unsafe(
                    token,
                    max_age=_get_config_or_default("QUART_AUTH_DURATION", app)
                )
                log.warning("An expired token was used with auth_id=%s", auth_id)
                return None
            except BadSignature:
                return None
