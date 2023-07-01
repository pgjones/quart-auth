Quart-Auth
==========

|Build Status| |docs| |pypi| |python| |license|

Quart-Auth is an extension for `Quart
<https://gitlab.com/pgjones/quart>`_ to provide for secure cookie
authentication (session management). It allows for a session to be
logged in, authenticated and logged out.

Usage
-----

To use Quart-Auth with a Quart app you have to create an QuartAuth and
initialise it with the application,

.. code-block:: python

    app = Quart(__name__)
    QuartAuth(app)

or via the factory pattern,

.. code-block:: python

    auth_manager = QuartAuth()

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

With QuartAuth initialised you can use the ``login_required``
function to decorate routes that should only be accessed by
authenticated users,

.. code-block:: python

    from quart_auth import login_required

    @app.route("/")
    @login_required
    async def restricted_route():
        ...

If no user is logged in, an ``Unauthorized`` exception is raised. To catch it,
install an error handler,

.. code-block:: python

    @app.errorhandler(Unauthorized)
    async def redirect_to_login(*_: Exception) -> ResponseReturnValue:
        return redirect(url_for("login"))

You can also use the ``login_user``, and ``logout_user`` functions to
start and end sessions for a specific ``AuthenticatedUser`` instance,

.. code-block:: python

    from quart_auth import AuthUser, login_user, logout_user

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

The user (authenticated or not) is available via the global
``current_user`` including within templates,

.. code-block:: python

    from quart import render_template_string
    from quart_auth import current_user

    @app.route("/")
    async def user():
        return await render_template_string("{{ current_user.is_authenticated }}")

Contributing
------------

Quart-Auth is developed on `GitHub
<https://github.com/pgjones/quart-auth>`_. You are very welcome to
open `issues <https://github.com/pgjones/quart-auth/issues>`_ or
propose `pull requests
<https://github.com/pgjones/quart-auth/pulls>`_.

Testing
~~~~~~~

The best way to test Quart-Auth is with Tox,

.. code-block:: console

    $ pip install tox
    $ tox

this will check the code style and run the tests.

Help
----

The Quart-Auth `documentation
<https://quart-auth.readthedocs.io>`_ is the best places to
start, after that try searching `stack overflow
<https://stackoverflow.com/questions/tagged/quart>`_ or ask for help
`on gitter <https://gitter.im/python-quart/lobby>`_. If you still
can't find an answer please `open an issue
<https://github.com/pgjones/quart-auth/issues>`_.


.. |Build Status| image:: https://github.com/pgjones/quart-auth/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/pgjones/quart-auth/commits/main

.. |docs| image:: https://img.shields.io/badge/docs-passing-brightgreen.svg
   :target: https://quart-auth.readthedocs.io

.. |pypi| image:: https://img.shields.io/pypi/v/quart-auth.svg
   :target: https://pypi.python.org/pypi/Quart-Auth/

.. |python| image:: https://img.shields.io/pypi/pyversions/quart-auth.svg
   :target: https://pypi.python.org/pypi/Quart-Auth/

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/pgjones/quart-auth/blob/main/LICENSE
