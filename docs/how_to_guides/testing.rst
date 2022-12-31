.. _testing:

Testing with Quart-Auth
=======================

Quart-Auth adds an authenticated method to the test client that can be
used as a context manager ensuring that there is an authenticated user
within. For example,

.. code-block::

    async def test_private_route():
         test_client = app.test_client()
         auth_id = "2"
         async with test_client.authenticated(auth_id):
             response = await test_client.get("/private")
             assert response.status_code == 200

This method is only usable in the cookie-mode. When using the
bearer-mode the authentication token must be added manually to the
request. There is a ``generate_auth_token`` method available on the
test client to make this easier,

.. code-block::

    async def test_private_route():
         test_client = app.test_client()
         auth_id = "2"
         token = test_client.generate_auth_token(auth_id)
         response = await test_client.get("/private", headers={"Authorization": f"bearer {token}"})
         assert response.status_code == 200
