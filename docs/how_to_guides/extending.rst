.. _extending:

Extending Quart-Auth
====================

Quart-Auth is meant to be extended, much like Quart (and Flask), a
good example of this is loading user data from a database,

.. code-block:: python

    from quart import Quart
    from quart_auth import AuthUser, AuthManager, current_user, login_required

    class User(AuthUser):
        def __init__(self, auth_id):
            super().__init__(auth_id)
            self._resolved = False
            self._email = None

        async def _resolve(self):
            if not self._resolved:
                self._email = await db.fetch_email(self.auth_id)
                self._resolved = True

        @property
        async def email(self):
            await self._resolve()
            return self._email

    auth_manager = AuthManager()
    auth_manager.user_class = User

    app = Quart(__name__)

    @app.route("/")
    @login_required
    async def index():
        return await current_user.email

    auth_manager.init_app(app)

If you are used to Flask-Login you are likely expecting the current_user
to be fully loaded without the extra resolve step, you can write
something like:

.. code-block:: python

    from quart import Quart
    from quart_auth import AuthUser, AuthManager, current_user, login_required

    class User(AuthUser):
        def __init__(self, auth_id):
            super().__init__(auth_id)
            self.email = None
            self.name = None

        async def load_user_data(self):
            user_data = await db.fetch_user_data(self.auth_id)

            self.email = user_data.get("email", None)
            self.name = user_data.get("name", None)

    auth_manager = AuthManager()
    auth_manager.user_class = User

    app = Quart(__name__)

    @app.route("/")
    @login_required
    async def index():
        return current_user.email

    auth_manager.init_app(app)

    @app.before_request
    @app.before_websocket
    async def load_full_user_data():
        await current_user.load_user_data()
