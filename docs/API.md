# Endpoints

This section lists the endpoints made available by a Labrys Blade. Each endpoint is listed together with a description of what the endpoint is for, all of the verbs that are available for that endpoint, and a description of the behavior provided by that verb.

## /identity

The `identity` endpoints provide all of the main info about a user, and allows identity server operations to take place.

### GET /identity

Get the public bio of the person running the blade. This should include relevant link tags for the authentication process.

### GET /identity/authenticate

Params: requester, state, return_address

Used to log the user in during the authentication process.

#### Requester Parameter

The `requester` parameter indicates the server that wants the user to authenticate.

#### State Parameter

The `state` parameter is some random data supplied by the requester to ensure that meddler-in-the-middle attacks don't occur.

#### Return Address Parameter

The `return_address` parameter is used to keep track of the location that the user should eventually be directed to once the requester has received authentication of the user's identity.

### POST /identity/authenticate

Used to verify codes during the authentication process.
