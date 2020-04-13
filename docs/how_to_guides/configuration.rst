.. _configuration:

Configuring Quart-Auth
======================

The following configuration options are used by Quart-Auth. They
should be set as part of the standard `Quart configuration
<https://pgjones.gitlab.io/quart/how_to_guides/configuration.html>`_.

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

Secret key
----------

Quart also requires the app to have a secret key set ``SECRET_KEY`` in
the Quart configuration. If you are unsure how to create a secret key
use this snippet,

.. code-block:: python

    >>> import secrets
    >>> secrets.token_urlsafe(16)
