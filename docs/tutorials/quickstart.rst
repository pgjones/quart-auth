.. _quickstart:

Quickstart
==========

Login, Logout and login required
---------------------------------

This is a quick example that has a route to log users in, another to
log them out and finally a route that can only be accessed by logged
in users.

.. code-block:: python

    from quart import Quart
    from quart_auth import (
        AuthUser, current_user, login_required, login_user, logout_user
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
