.. _mode:

Which mode?
===========

The default Quart-Auth cookie-mode is to store and read authentication
information from a cookie. This mode is best used when the client is a
web browser, including for Single Page Apps.

An alternative bearer-mode requires the authentication information to
be present in a Bearer-Authorization header. This mode is best used
when the client is not a web browser e.g. a programatic script.
