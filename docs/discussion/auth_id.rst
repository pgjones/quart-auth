.. _auth_id:

Auth ID meaning
===============

Quart-Auth stores uses a ``str``, ``auth_id`` for authentication. This
ID can be anything that can uniquely identify (authenticate) a
user. An obvious example would be to use the user's ID as the
``auth_id``. However it is better to not use the user's ID in case the
user's session is compromised e.g. via a stolen phone, as the
``auth_id`` itself most be revoked to disable the session.

The ``auth_id`` is a ``str`` rather than a ``int`` to allow for uuids
to be used (or something else), if you expect to use an ``int`` be
sure to cast (and check for ValueErrors).
