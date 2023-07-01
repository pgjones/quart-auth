.. _multiple_auth:

Multiple authentication schemes
===============================

At times it may be required to have multiple authentication schemes,
for example if your application supports separated staff and admin
logins. Quart-Auth supports this via the usage of multiple
non-singleton instances.

.. note::

   The documentation throughout assumes a single, singleton, instance
   is being used except on this page.

To utilise this feature you can setup multiple non-singleton
instances, for example,

.. code-block:: python

    from quart_auth import QuartAuth

    staff_auth = QuartAuth(
        app, attribute_name="staff", cookie_name="STAFF", salt="staff salt", singleton=False
    )
    admin_auth = QuartAuth(
        app, attribute_name="admin", cookie_name="ADMIN", salt="admin salt", singleton=False
    )

The unique naming is critical if you wish to avoid security vulnerabilities.

The existing global functions all map to methods on the ``QuartAuth``
class with the exception of ``login_required`` and
``current_user``. These can be implmeneted as follows,

.. code-block:: python

    from werkzeug.local import LocalProxy

    current_staff = LocalProxy(lambda: staff_auth.load_user())

    def staff_login_required(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await current_staff.is_authenticated:
                raise Unauthorized()
            else:
                return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    current_admin = LocalProxy(lambda: admin_auth.load_user())

    def admin_login_required(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await current_admin.is_authenticated:
                raise Unauthorized()
            else:
                return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

As a warning/reminder when logging a user in, be sure to set the
action to ``WRITE`` or ``WRITE_PERMANENT`` as makes sense to you, i.e.

.. code-block:: python

    @app.post("/staff/login/")
    async def login_staff() -> ResponseReturnValue:
        ...
        staff_auth.login_user(AuthUser("2", Action.WRITE))
