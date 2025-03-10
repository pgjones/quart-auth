0.11.1 (Unreleased)
-------------------

* Flask backport: Fix signing key selection order when key rotation is enabled
  via ``SECRET_KEY_FALLBACKS``.
  <https://github.com/pallets/flask/security/advisories/GHSA-4grg-w6v8-c28g>

0.11.0 2024-12-26
-----------------

* Support SECRET_KEY_FALLBACKS when loading tokens to allow for key
  rotation.
* Bugfix ensure user_class is used if set in QuartAuth constructor.
* Support Python 3.13, drop Python 3.8.

0.10.1 2024-05-18
-----------------

* Bugfix don't override a user set user_class or serializer_class.

0.10.0 2024-05-18
-----------------

* Bugfix the Serializer init type hinting
* Update extention init typing to match docs and code.
* Allow the user_class and serializer_class to be specified in the
  constructor.

0.9.1 2024-01-28
----------------

* Bugfix decorator type hinting.
* Bugfix after_{request,websocket} function typing.
* Display some helpful warnings for development usage.

0.9.0 2023-07-02
----------------

* Support multiple authentication schemes, whilst supporting a default
  singleton global. This renames ``AuthManager`` -> ``QuartAuth`` and
  removes the TestClient ``authenticated`` and ``generate_auth_token``
  methods - use the ``authenticated_client`` and ``generate_auth_token``
  functions instead.

0.8.0 2023-01-01
----------------

* Utilise the extensions app attribute. The ``app.auth_manager`` is no
  longer used, instead use ``app.extensions["QUART_AUTH"]``.
* Allow the token to be customised if desired.
* Add a bearer mode to allow for non-cookie based authentication. This
  change will cause all existing tokens to be invalid, requiring a new
  login.
* Support Python 3.11

0.7.0 2022-07-23
----------------

* Require Quart >= 0.18
* Switch to GitHub rather than GitLab.

0.6.0 2021-11-10
----------------

* Support Python 3.10
* Add a basic_auth_required decorator.

0.5.0 2021-05-11
----------------

* Support authenticating WebSocket connections.
* Make testing with logged in users easier via a
  test_client.authenticated context manager.
* Ensure wrapped routes are async.

0.4.0 2020-07-14
----------------

* Bugfix set domain when deleting auth cookie.
* Change the default SameSite from Strict to Lax.
* Change the default hashing algorithm to SHA512. This will invalidate
  any existing cookies.
* Switch from setting expires to max age.
* Add a renew_login function, to renew the cookie expiry.
* Ensure cookies are deleted - by using the same samesite attribute as
  configured.
* Require Quart >= 0.13

0.3.0 2020-04-14
----------------

* Add current_user as a template context - to allow its usage when
  rendering templates.
* Introduce a Quart-Auth specific Unauthorized exception - to allow
  specific actions when unauthorized requests are made e.g. redirects.

0.2.0 2020-03-13
----------------

* Loosen python version requirement - now requires Python >= 3.7.
* Ensure the current_user resolves to an Unauthenticated user on
  logout.
* Refactor User classes remove AnnonymousUser and UserABC, use only
  AuthUser.

0.1.0 2020-03-08
----------------

* Released initial alpha version.
