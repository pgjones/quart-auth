.. _quickstart:

Quickstart
==========

Login, Logout and login required (cookie-mode)
----------------------------------------------

This is a quick example that demonstrates how to best use Quart-Auth
with web browser clients. It has a route to log users in, another to
log them out and finally a route that can only be accessed by logged
in users.

.. code-block:: python

    from quart import Quart, render_template_string, websocket
    from quart_auth import (
        AuthUser, AuthManager, current_user, login_required, login_user, logout_user
    )

    app = Quart(__name__)
    app.secret_key = "secret key"  # Do not use this key

    AuthManager(app)

    @app.route("/login")
    async def login():
        # Check Credentials here, e.g. username & password.
        ...
        # We'll assume the user has an identifying ID equal to 2
        login_user(AuthUser(2))
        ...

    @app.route("/logout")
    async def logout():
        logout_user()
        ...

    @app.route("/")
    @login_required
    async def restricted_route():
        current_user.auth_id  # Will be 2 given the login_user code above
        ...

    @app.route("/hello")
    async def hello():
        return await render_template_string("""
        {% if current_user.is_authenticated %}
          Hello logged in user
        {% else %}
          Hello logged out user
        {% endif %}
        """)

    @app.websocket("/ws")
    @login_required
    async def ws():
         await websocket.send(f"Hello {current_user.auth_id}")
         ...

Login, restricted routes (bearer-mode)
--------------------------------------

This is a quick example that demonstrates how to best use Quart-Auth
with API clients. It has a route to exchange login information for a
bearer token and routes that can only be accessed with a valid bearer
token.

.. code-block:: python

    from quart import Quart, render_template_string, websocket
    from quart_auth import (
        AuthUser, AuthManager, current_user, login_required, login_user, logout_user
    )

    app = Quart(__name__)
    app.config["QUART_AUTH_MODE"] = "bearer"
    app.secret_key = "secret key"  # Do not use this key

    auth_manager = AuthManager(app)

    @app.route("/login")
    async def login():
        # Check Credentials here, e.g. username & password.
        ...
        # We'll assume the user has an identifying ID equal to 2
        token = auth_manager.dump_token("2")
        return {"token": token}

    @app.route("/")
    @login_required
    async def restricted_route():
        current_user.auth_id  # Will be 2 given the login_user code above
        ...

    @app.route("/hello")
    async def hello():
        return await render_template_string("""
        {% if current_user.is_authenticated %}
          Hello logged in user
        {% else %}
          Hello logged out user
        {% endif %}
        """)

    @app.websocket("/ws")
    @login_required
    async def ws():
         await websocket.send(f"Hello {current_user.auth_id}")
         ...

Note that the client is required to pass the token in a Authorization
header with the bearer prefix.


Basic auth
----------

This is a quick example that demonstrates how to best use Quart-Auth
with basic API clients or basic web browsers. It has a route
restricted by basic authentication, i.e. it can only be accessed by
requests that have the correct basic auth credentials.

.. code-block:: python

    from quart import Quart
    from quart_auth import basic_auth_required

    app = Quart(__name__)
    app.config["QUART_AUTH_BASIC_USERNAME"] = "user"
    app.config["QUART_AUTH_BASIC_PASSWORD"] = "password"  # Do not use this password
    app.secret_key = "secret key"  # Do not use this key

    AuthManager(app)

    @app.route("/")
    @basic_auth_required
    async def restricted_route():
        ...  # Only called if
