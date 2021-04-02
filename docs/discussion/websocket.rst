.. _websocket:

WebSocket Authentication
========================

Quart-Auth can be used to authenticate WebSocket connections, however
as cookies cannot be reliably set with a WebSocket connection it is
not possible to login or logout users via a WebSocket connection.
