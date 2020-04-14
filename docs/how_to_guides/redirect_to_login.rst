.. _redirect_to_login:

Redirect to login
=================

Rather than returning a 401 unauthorized response you may wish instead
to return a 302 redirect response, redirecting the visitor to the
login page. To do so simply catch the Quart-Auth ``Unauthorized``
exception and return the appropriate redirect,

.. code-block:: python

    from quart import redirect, url_for
    from quart_auth import Unauthorized

    @app.errorhandler(Unauthorized)
    async def redirect_to_login(*_):
        return redirect(url_for("login"))
