.. _configuration:

Configuring Quart-Auth
======================

The following configuration options are used by Quart-Auth. They
should be set on initialisation of :class:`~quart.QuartAuth` or as
part of the standard `Quart configuration
<https://pgjones.gitlab.io/quart/how_to_guides/configuration.html>`_.

================ ============================ ======================= ===================
Init argument    Configuration key            type                    default
---------------- ---------------------------- ----------------------- -------------------
cookie_domain    QUART_AUTH_COOKIE_DOMAIN     str | None              None
cookie_name      QUART_AUTH_COOKIE_NAME       str                     "QUART_AUTH"
cookie_path      QUART_AUTH_COOKIE_PATH       str                     /
cookie_http_only QUART_AUTH_COOKIE_HTTP_ONLY  bool                    True
cookie_samesite  QUART_AUTH_COOKIE_SAMESITE   None | "Strict" | "Lax" "Lax"
cookie_secure    QUART_AUTH_COOKIE_SECURE     bool                    True
duration         QUART_AUTH_DURATION          int                     365 * 24 * 60 * 60
mode             QUART_AUTH_MODE              "cookie" | "bearer"     "cookie"
salt             QUART_AUTH_SALT              str                     "quart auth salt"
================ ============================ ======================= ===================

The ``COOKIE`` related options refer directly to standard cookie
options. In development it is likely that you'll need to set
``QUART_AUTH_COOKIE_SECURE`` to ``False``.

Secret key
----------

Quart also requires the app to have a secret key set ``SECRET_KEY`` in
the Quart configuration. If you are unsure how to create a secret key
use this snippet,

.. code-block:: python

    >>> import secrets
    >>> secrets.token_urlsafe(16)
