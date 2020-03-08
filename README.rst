Quart-Auth
==========

|Build Status| |pypi| |python| |license|

Quart-Auth is an extension for `Quart
<https://gitlab.com/pgjones/quart>`_ to provide for secure cookie
authentication (session management). It allows for a session to be
logged in, authenticated and logged out.

Usage
-----

To use Quart-Auth with a Quart app you have to create an AuthManager and
initialise it with the application,

.. code-block:: python

    app = Quart(__name__)
    AuthManager(app)

or via the factory pattern,

.. code-block:: python

    auth_manager = AuthManager()

    def create_app():
        app = Quart(__name__)
        auth_manager.init_app(app)
        return app

In addition you will need to configure Quart-Auth, which defaults to
the most secure. At a minimum you will need to set secret key,

.. code-block:: python

    app.secret_key = "secret key"  # Do not use this key

which you can generate via,

.. code-block:: python

    >>> import secrets
    >>> secrets.token_urlsafe(16)

Tou may also need to disable secure cookies to use in development, see
configuration below.

With AuthManager initialised you can use the ``login_required``
function to decorate routes that should only be accessed by
authenticated users,

.. code-block:: python

    @app.route("/")
    @login_required
    async def restricted_route():
        ...

You can also use the ``login_user``, and ``logout_user`` functions to
start and end sessions for a specific ``AuthenticatedUser`` instance,

.. code-block:: python

    @app.route("/login")
    async def login():
        # Check Credentials here, e.g. username & password.
        ...
        # We'll assume the user has an identifying ID equal to 2
        login_user(AuthenticatedUser(2))
        ...

    @app.route("/logout")
    async def logout():
        logout_user()
        ...

Extending Quart-Auth
--------------------

Quart-Auth is meant to be extended, much like Quart (and Flask), a
good example of this is loading user data from a database,

.. code-block:: python

    from quart import Quart
    from quart_auth import AuthenticatedUser, AuthManager, current_user, login_required

    class User(AuthenticatedUser):
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

.. note::

    If you are used to Flask-Login you are likely expecting the
    current_user to be fully loaded without the extra resolve
    step. This is not possible in Quart-Auth as the ``current_user``
    is loaded synchronously whereas the User is assumed to be loaded
    asynchronously i.e. ``await current_user.email`` is preferred over
    ``(await current_user).email``.

Auth ID
~~~~~~~

Quart-Auth authenticates using a ``str``, ``auth_id``, which can be
set to the User ID. It is better not use the user's ID in case the
user's session is compromised e.g. via a stolen phone, as the
``auth_id`` itself most be revoked to disable the session.

Configuration
-------------

The following configuration options are used by Quart-Auth,

============================ ============================= ===================
Configuration key            type                          default
---------------------------- ----------------------------- -------------------
QUART_AUTH_COOKIE_DOMAIN     Optional[str]                 None
QUART_AUTH_COOKIE_NAME       str                           QUART_AUTH
QUART_AUTH_COOKIE_PATH       str                           /
QUART_AUTH_COOKIE_HTTP_ONLY  bool                          True
QUART_AUTH_COOKIE_SAMESITE   Union[None, "Strict", "Lax"]  Strict
QUART_AUTH_COOKIE_SECURE     bool                          True
QUART_AUTH_DURATION          int                           365 * 24 * 60 * 60
QUART_AUTH_SALT              str                           quart auth salt
============================ ============================= ===================

The ``COOKIE`` related options refer directly to standard cookie
options. In development it is likely that you'll need to set
``QUART_AUTH_COOKIE_SECURE`` to ``False``.

Contributing
------------

Quart-Auth is developed on `GitLab
<https://gitlab.com/pgjones/quart-auth>`_. You are very welcome to
open `issues <https://gitlab.com/pgjones/quart-auth/issues>`_ or
propose `merge requests
<https://gitlab.com/pgjones/quart-auth/merge_requests>`_.

Testing
~~~~~~~

The best way to test Quart-Auth is with Tox,

.. code-block:: console

    $ pip install tox
    $ tox

this will check the code style and run the tests.

Help
----

This README is the best place to start, after that try opening an
`issue <https://gitlab.com/pgjones/quart-auth/issues>`_.


.. |Build Status| image:: https://gitlab.com/pgjones/quart-auth/badges/master/pipeline.svg
   :target: https://gitlab.com/pgjones/quart-auth/commits/master

.. |pypi| image:: https://img.shields.io/pypi/v/quart-auth.svg
   :target: https://pypi.python.org/pypi/Quart-Auth/

.. |python| image:: https://img.shields.io/pypi/pyversions/quart-auth.svg
   :target: https://pypi.python.org/pypi/Quart-Auth/

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://gitlab.com/pgjones/quart-auth/blob/master/LICENSE
