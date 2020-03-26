# Endpoints

This section lists the endpoints made available by a Labrys Blade. Each endpoint is listed together with a description of what the endpoint is for, all of the verbs that are available for that endpoint, and a description of the behavior provided by that verb.

## /identity

The `identity` endpoints provide all of the main info about a user, and allows identity provider operations to take place.

### GET /identity

Get the public bio of the person running the blade. This should include relevant link tags for the authentication process.

### GET /identity/<path:filename>

Get the relevant file. This is used simply to get specific profile properties such as the display name or bio.

### GET /identity/deauthenticate

Deautheticate the user from the blade by removing any set cookies.

### GET /identity/authenticate

Params: optional(requester, state, return_address)

Used to log the user in during the authentication process. All parameters are optional, but linked, i.e. either you make a request with no parameters or all of them.

With no parameters, the user is simply authenticated with the blade.

With parameters, the user is authenticated as part of a multi-step authentication process and forwarded to the return address. The forward includes information including an auth token to be used in a subsequent `GET` request to `/identity/verify`.

#### Requester Parameter

The `requester` parameter indicates the blade that wants the user to authenticate.

#### State Parameter

The `state` parameter is some random data supplied by the requester to ensure that meddler-in-the-middle attacks don't occur.

#### Return Address Parameter

The `return_address` parameter is used to keep track of the location that the user should eventually be directed to once the requester has received authentication of the user's identity.

### POST /identity/authenticate

Params: password

Used to submit authenticating password to the blade as part of the auth process.

### GET /identity/verify

Params: (auth_token, requester, state)

Used as part of the identity authentication process to verify that a user who claims to have authenticated with this blade as their identity provider did in fact do so.

#### Auth Token Parameter

The `auth_token` parameter is a piece of data used as part of the authentication process to witness that the user did indeed authenticate with the blade. The supplied auth token must match the one the blade issued to the user in order for the user to be considered authenticated.

#### Requester Parameter

The `requester` parameter indicates the blade that wants the user to authenticate.

#### State Parameter

The `state` parameter is some random data supplied by the requester to ensure that meddler-in-the-middle attacks don't occur.

### GET /identity/public_signing_key

Gets the public signing key for the blade. Use as part of the process of establishing the unique identity of the blade.

### GET /identity/sign

Params: message

Used to verify the identity of a blade. The message is signed with the private key corresponding to the public signing key at `/identity/public_signing_key` and then returned to the user.
