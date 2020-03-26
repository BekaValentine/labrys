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

## /inbox

The `inbox` endpoint acts similar to an ActivityPub inbox, in that it is both the place that an external user can send push content and also the place that the owner gets retrieve pushed content from.

### GET /inbox

Returns a feed of summaries of all of the messages sent to the blade.

### GET /inbox/<id>

Returns the message with id `id`.

### POST /inbox

Adds a new message to the blade's inbox.

## /outbox

The `outbox` endpoint acts similar to an ActivityPub outbox, in that it is both the place that an external user can pull content and also the place that the owner publish content to. This is also where the user puts messages to be pushed to other users.

### GET /outbox

Params: optional(start_after), optional(count)

Returns the feed for the blade.

#### Start After Param

The id of the last message before the first message desired. That is to say, when arranged in order of publish datetime, the first message to be returned should be the message just before the designated message. When not provided, it's assumed that the user agent is requesting the most recent messages.

#### Count Param

The number of messages to return, defaulting to 10. The messages returned after the next oldest messages after the start message.

### POST /outbox

Content: The message to publish.

If the message is a private message, it will be automatically forwarded to the recipient's inbox.

## /subscriptions

The `subscriptions` endpoint is like Twitter's `following` list, except that it's not public. It manages which other blades this blade is pulling feeds from.

### GET /subscriptions

Returns the list of blade that this blade is subscribed to.

### POST /subscriptions

Adds a new blade to the subscriptions list.

### DELETE /subscriptions/<id>

Removes the designated blade from the subscription list.

## /permissions

The `permissions` endpoint is like Twitter's `followers` list, except that it's not public. It manages which other blades can pull what feeds from this blade.

### GET /permissions/groups

Returns the list of group summaries.

### GET /permissions/groups/<id>

Returns the info on the designed group.

### PATCH /permissions/groups/<id>

Updates the designated group.

### DELETE /permissions/groups/<id>

Deletes the designated group.

### POST /permissions/groups

Adds a new permissions group.

### GET /permissions/blades

Returns the list of blades with special permissions.

### POST /permissions/blades

Adds a permitted blade.

### GET /permissions/blades/<id>

Returns the permissions info for the designated blade.

### PATCH /permissions/blades/<id>

Updates the designated blade permissions.

### DELETE /permissions/blades/<id>

Removes the designated blade's permissions.

## /timeline

The `timeline` endpoint acts as a way of retrieving the content of all the blade's subscriptions' outboxes. The blade will download all of the messages ahead of time and store them locally on it in the background.

### GET /timeline

Params: optional(start_after), optional(count)

Returns the outbox messages for all of the blade's subscriptions.

#### Start After Param

The id of the last message before the first message desired. That is to say, when arranged in order of publish datetime, the first message to be returned should be the message just before the designated message. When not provided, it's assumed that the user agent is requesting the most recent messages.

#### Count Param

The number of messages to return, defaulting to 10. The messages returned after the next oldest messages after the start message.
