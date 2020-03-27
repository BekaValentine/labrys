# Endpoints

This section lists the endpoints made available by a Labrys Blade. Each endpoint is listed together with a description of what the endpoint is for, all of the verbs that are available for that endpoint, and a description of the behavior provided by that verb.

## /identity

The `identity` endpoints provide all of the main info about a user, and allows identity provider operations to take place.

### GET /identity/avatar : Image

Get the blade's avatar, if it exists.

### GET /identity/display_name : String

Get the blade's display name.

### GET /identity/bio : String

Get the blade's bio.

### GET /identity/public_signing_key : PublicKey

Gets the public signing key for the blade. Use as part of the process of establishing the unique identity of the blade.

### GET /identity/sign : String -> String

Params: message

Used to verify the identity of a blade. The message is signed with the private key corresponding to the public signing key at `/identity/public_signing_key` and then returned to the user.

### GET /identity/deauthenticate : ()

Deautheticate the user from the blade by removing any set cookies.

### GET /identity/authenticate : ()

Used to log the user in during the authentication process. All parameters are optional, but linked, i.e. either you make a request with no parameters or all of them.

### POST /identity/authenticate : Password -> ()

Params: password

Used to submit authenticating password to the blade as part of the auth process.

## /inbox

The `inbox` endpoint acts similar to an ActivityPub inbox, in that it is both the place that an external user can send push content and also the place that the owner gets retrieve pushed content from.

### GET /inbox : List MessageSummary

Returns a feed of summaries of all of the messages sent to the blade.

### GET /inbox/<id> : MessageID -> Message

Returns the message with id `id`.

### POST /inbox : Message -> ()

Adds a new message to the blade's inbox.

## /outbox

The `outbox` endpoint acts similar to an ActivityPub outbox, in that it is both the place that an external user can pull content and also the place that the owner publish content to. This is also where the user puts messages to be pushed to other users.

### GET /outbox : (Maybe MessageID, Maybe Nat) -> List MessageSummary

Params: optional(start_after), optional(count)

Returns the feed for the blade.

#### Start After Param

The id of the last message before the first message desired. That is to say, when arranged in order of publish datetime, the first message to be returned should be the message just before the designated message. When not provided, it's assumed that the user agent is requesting the most recent messages.

#### Count Param

The number of messages to return, defaulting to 10. The messages returned after the next oldest messages after the start message.

### POST /outbox : Message -> ()

Content: The message to publish.

If the message is a private message, it will be automatically forwarded to the recipient's inbox.

## /subscriptions

The `subscriptions` endpoint is like Twitter's `following` list, except that it's not public. It manages which other blades this blade is pulling feeds from.

### GET /subscriptions : List Subscription

Returns the list of blade that this blade is subscribed to.

### POST /subscriptions : Subscription -> ()

Adds a new blade to the subscriptions list.

### DELETE /subscriptions/<id> : SubscriptionID -> ()

Removes the designated blade from the subscription list.

## /permissions

The `permissions` endpoint is like Twitter's `followers` list, except that it's not public. It manages which other blades can pull what feeds from this blade.

### GET /permissions/groups : List PermissionGroupSummary

Returns the list of group summaries.

### POST /permissions/groups : PermissionGroup -> ()

Adds a new permissions group.

### GET /permissions/groups/<id> : PermissionGroupID -> PermissionGroup

Returns the info on the designed group.

### PATCH /permissions/groups/<id> : (PermissionGroupID, PermissionGroup) -> ()

Updates the designated group.

### DELETE /permissions/groups/<id> : PermissionGroupID -> ()

Deletes the designated group.

### GET /permissions/blades : List PermissionBladeSummary

Returns the list of blades with special permissions.

### POST /permissions/blades : PermissionBlade -> ()

Adds a permitted blade.

### GET /permissions/blades/<id> : PermisionBladeID -> PermissionBlade

Returns the permissions info for the designated blade.

### PATCH /permissions/blades/<id> : (PermissionBladeID, PermissionBlade) -> ()

Updates the designated blade permissions.

### DELETE /permissions/blades/<id> : PermissionBladeID -> ()

Removes the designated blade's permissions.

## /timeline

The `timeline` endpoint acts as a way of retrieving the content of all the blade's subscriptions' outboxes. The blade will download all of the messages ahead of time and store them locally on it in the background.

### GET /timeline : (Maybe MessageID, Maybe Nat) -> List MessageSummary

Params: optional(start_after), optional(count)

Returns the outbox messages for all of the blade's subscriptions.

#### Start After Param

The id of the last message before the first message desired. That is to say, when arranged in order of publish datetime, the first message to be returned should be the message just before the designated message. When not provided, it's assumed that the user agent is requesting the most recent messages.

#### Count Param

The number of messages to return, defaulting to 10. The messages returned after the next oldest messages after the start message.

## /message_types

The `message_types` endpoint is for managing the ontology that the blade makes use of. Message types can be added implicitly by using new ones in outgoing messages, as well as added explicitly via the endpoint.

### GET /message_types : List MessageTypeSummary

Returns a list of message type summaries.

### POST /message_type : MessageType -> ()

Adds a new message type.

### GET /message_type/<id> : MessageTypeID -> MessageType

Gets the designated message type.

### PATCH /message_type/<id> : (MessageTypeId, MessageType) -> ()

Updates the designated message type.

# Types

The following types are used in various places in the API.

## Identity

```
{ display_name : String
, bio : String
}
```

## Message

```
{ id : MessageID
, sender : BladeID
, receiver : BladeID
, type : MessageType
, content : Content
}
```

## MessageSummary

```
{ id : MessageID
, sender : BladeID
, receiver: BladeID
, type : MessageType
, contentSummary : ContentSummary
}
```

## Subscription

```
{ id : SubscriptionID
, blade : BladeID
, identity : Identity
}
```

## PermissionGroup

```
{ id : PermissionGroupID
, name : String
, description : String
, members : List BladeID
, permissions : List Permission
}
```

## PermissionGroupSummary

```
{ id : PermissionGroupID
, name : String
, description : String
, member_count : Nat
}
```

## PermissionBlade

```
{ blade : Blade
, permissions : List Permission
}
```

## PermissionBladeSummary

## MessageType

```
{ id : MessageTypeID
, name : String
, description : String
, fields : List String
, defining_url : Maybe URL
}
```

## MessageTypeSummary

```
{ id : MessageTypeID
, name : String
, description : String
}
```
