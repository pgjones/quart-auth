.. _design_choices:

Design choices
==============

session usage
-------------

Quart-Auth does not use the ``session`` available via Quart so as to
ensure there are no naming conflicts (with other users of the session)
and to ensure that the cookie is configured as desired, rather than
reconfigured by another part of the Quart app.

Auth ID meaning
---------------

The ``auth_id`` is a ``str`` rather than a ``int`` to allow for uuids
to be used (or something else), if you expect to use an ``int`` be
sure to cast (and check for ValueErrors).

The ``auth_id`` is so called, rather than being called a ``user_id``
to discourage the use of the user's ID. This makes it easier to revoke
the quart-auth session, as to do so the ``auth_id`` must be marked as
invalid which would require disabling the user's account if the user's
ID was used.
