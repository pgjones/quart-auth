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
