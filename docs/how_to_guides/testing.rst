.. _testing:

Testing with Quart-Auth
=======================

Quart-Auth adds an authenticated method to the test client that can be
used as a context manager ensuring that there is an authenticated user
within. For example,

.. code-block::

    from quart_auth import authenticated_client

    async def test_private_route():
         test_client = app.test_client()
         auth_id = "2"
         async with authenticated_client(test_client, auth_id):
             response = await test_client.get("/private")
             assert response.status_code == 200

This method is only usable in the cookie-mode. When using the
bearer-mode the authentication token must be added manually to the
request. There is a ``generate_auth_token`` function available to make
this easier,

.. code-block::

    from quart_auth import generate_auth_token

    async def test_private_route():
         test_client = app.test_client()
         auth_id = "2"
         token = generate_auth_token(test_client, auth_id)
         response = await test_client.get("/private", headers={"Authorization": f"bearer {token}"})
         assert response.status_code == 200
