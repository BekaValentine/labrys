# Endpoints

This section lists the endpoints made available by a Labrys Blade. Each endpoint
is listed together with a description of what the endpoint is for,  all of the
verbs that are available for that endpoint, and a description of the behavior
provided by that verb.



## <domain>/identity

The `identity.<domain>` endpoints provide all of the main info about a user, and
allows identity server operations to take place.


### GET <domain>/identity

Get the public bio of the person running the blade. This should include relevant
link tags for the indieauth authentication process.


### GET <domain>/identity/authenticate

Params: requester, state, return_address

Used to log the user in during the indieauth authentication process.

#### Requester Parameter

The `requester` parameter indicates the server that wants the user to
authenticate.

#### State Parameter

The `state` parameter is some random data supplied by the requester to ensure
that meddler-in-the-middle attacks don't occur.

#### Return Address Parameter

The `return_address` parameter is used to keep track of the location that the user
should eventually be directed to once the requester has received authentication
of the user's identity.


### POST <domain>/identity/authenticate

Used to verify codes during the indieauth authentication process.



## www.<domain>

The `www.<domain>` endpoint is for the public website of the blade, and acts
like a general purpose website. This endpoint passes all verbs along to the
general purpose server.



## subscription.<domain>

The `subscription.<domain>` endpoint is how external users can subscribe to a
blade's content, and provides a means to register with the blade.


### GET subscription.<domain>

Get information about the subscription, including what apps are available to the
user.

AUTHENTICATION REQUIRED


### GET subscription.<domain>/request

Gets the status of a subscription request

ID SERVER INFO REQUIRED


### POST subscription.<domain>/request

Makes a new subscription request if there isn't one already pending. Does
nothing if the request is from a blocked ID server.

ID SERVER INFO REQUIRED



## apps.<domain>

The `apps.<domain>` endpoint provides info about the apps that the user can
access on the blade. It returns a list of app descriptions, which contain the
app name, app description, and app endpoint (which is of the form
`apps.<domain>/<app-id>`).

AUTHENTICATION REQUIRED


### apps.<domain>/<app-id>

The `apps.<domain>/<app-id>` endpoint forwards all verbs to the app server.



## admin.<domain>

The `admin.<domain>` endpoint serves an administrative frontend. This endpoint
passes all verbs along to the admin server.
