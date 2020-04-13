.. _resolving:

Resolving users
===============

It is common, for example in Flask-Login, for the ``current_user`` to
contain a full User model's data (email, name, etc...). This is
possible in Quart-Auth as well, but it requires an extra resolve
step. This is a design choice, that can be summarised as ``await
current_user.email`` being preferred over ``(await
current_user).email``.

The design choice is that the properties of the ``current_user``
should be awaited, rather than the ``current_user`` itself. This
should match your expectations.
