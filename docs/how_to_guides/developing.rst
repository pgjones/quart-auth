.. _developing:

Developing with Quart-Auth
==========================

The configuration defaults are meant for a production environment and
should be secure by default. When developing it is helpful to change a
few of these settings, most notably setting ``cookie_secure`` or
``QUART_AUTH_COOKIE_SECURE`` to ``False`` as the development server
does not default to HTTPS.
