.. _basic_auth:

Basic Authentication
====================

Basic authentication is a simple technique to authorise requests by
providing a username and password with the request. To require basic
auth credentials for a route (or websocket) use the
``basic_auth_required`` decorator,

.. code-block:: python

    from quart_auth import basic_auth_required

    @app.route("/")
    @basic_auth_required()
    async def index():
        ...

The username and password must be specified in the configuration, by
default by the ``QUART_AUTH_BASIC_USERNAME`` and
``QUART_AUTH_BASIC_PASSWORD`` keys. However you can choose different
keys, e.g. ``CUSTOM_USERNAME`` and ``CUSTOM_PASSWORD`` via arguments
to the decorator,

.. code-block:: python

    from quart_auth import basic_auth_required

    @app.route("/")
    @basic_auth_required(username_key="CUSTOM_USERNAME", password_key="CUSTOM_PASSWORD")
    async def index():
        ...

If the request does not provide valid credentials an
``UnauthorizedBasicAuth`` exception will be raised.
