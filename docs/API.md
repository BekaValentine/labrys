# Endpoints

This section lists the endpoints made available by a Labrys Blade. Each endpoint is listed together with a description of what the endpoint is for, all of the verbs that are available for that endpoint, and a description of the behavior provided by that verb.

## /api/identity

The `identity` endpoints provide all of the main info about a user, and allows identity provider operations to take place.

### GET /api/identity/avatar : Image

Get the blade's avatar, if it exists.

### GET /api/identity/display_name : String

Get the blade's display name.

### GET /api/identity/bio : String

Get the blade's bio.

### GET /api/identity/public_signing_key : PublicKey

Gets the public signing key for the blade. Use as part of the process of establishing the unique identity of the blade.

### GET /api/identity/sign : String -> String

Params: message

Used to verify the identity of a blade. The message is signed with the private key corresponding to the public signing key at `/identity/public_signing_key` and then returned to the user.

### GET /api/identity/deauthenticate : ()

Deautheticate the user from the blade by removing any set cookies.

### POST /api/identity/authenticate : Password -> ()

Params: password

Used to submit authenticating password to the blade as part of the auth process.

## /api/inbox

The `inbox` endpoint is the place that an external user can send private message notifications to.

### GET /api/inbox : List InboxMessage

Returns a list of all of the private messages sent to the blade.

### POST /api/inbox : BladeID -> ()

Notifies the receiving blade that the blade with the given ID has new messages for it, which are then pulled from the sending blade.

### GET /api/inbox/<id> : InboxMessageID -> Message

Returns the inbox message with id `id`.

### DELETE /api/inbox/<id> : InboxMessageID -> ()

Deletes the designated inbox message.

## /api/outbox

The `outbox` endpoint acts as the place that the owner publishes messages to send to other blades' inboxes.

### GET /api/outbox : List OutboxMessage

Gets all the messages currently in the outbox. If the user is the blade owner, it'll show all of the messages. If the user is not the blade owner, then it will show all the messages for the requesting blade.

### POST /api/outbox : OutboxMessage -> ()

Sends the message.

Content: The message to send.

### DELETE /api/outbox/<id> : OutboxMessageID -> ()

Deletes the specified message.

## /api/feed

The feed is the list of broadcast-style messages.

### GET /api/feed : (Maybe FeedMessageID) -> List FeedMessage

Params: optional(last_seen)

Returns the feed for the blade. If the `last_seen` query param is specified, only the messages with a later publish date will be returned.

#### Last Seen Param

The id of the most recent message that the requesting blade has seen.

### POST /api/feed : FeedMessage -> ()

Publishes a message.

Content: The message to publish.

### GET /api/feed/<id> : FeedMessage

Gets a feed message.

### DELETE /api/feed/<id> : FeedMessageID -> ()

Deletes the message with the specified id.

## /api/subscriptions

The `subscriptions` endpoint is like Twitter's `following` list, except that it's not public. It manages which other blades this blade is pulling feeds from.

### GET /api/subscriptions : List Subscription

Returns the list of blade that this blade is subscribed to.

### POST /api/subscriptions : Subscription -> ()

Adds a new blade to the subscriptions list.

### DELETE /api/subscriptions/<id> : SubscriptionID -> ()

Removes the designated blade from the subscription list.

## /api/permissions

The `permissions` endpoint is like Twitter's `followers` list, except that it's not public. It manages which other blades can pull what feeds from this blade.

### GET /api/permissions/groups : List PermissionsGroupSummary

Returns the list of group summaries.

### POST /api/permissions/groups : PermissionsGroup -> ()

Adds a new permissions group.

### GET /api/permissions/groups/<id> : PermissionsGroupID -> PermissionsGroup

Returns the info on the designed group.

### PUT /api/permissions/groups/<id> : (PermissionsGroupID, PermissionsGroup) -> ()

Updates the designated group.

### DELETE /api/permissions/groups/<id> : PermissionsGroupID -> ()

Deletes the designated group.

### GET /api/permissions/blades : List PermissionsBladeSummary

Returns the list of blades with special permissions.

### POST /api/permissions/blades : PermissionsBlade -> ()

Adds a permitted blade.

### GET /api/permissions/blades/<id> : PermisionBladeID -> PermissionsBlade

Returns the permissions info for the designated blade.

### PUT /api/permissions/blades/<id> : (PermissionsBladeID, PermissionsBlade) -> ()

Updates the designated blade permissions.

### DELETE /api/permissions/blades/<id> : PermissionsBladeID -> ()

Removes the designated blade's permissions.

## /api/timeline

The `timeline` endpoint acts as a way of retrieving the content of all the blade's subscriptions' outboxes. The blade will download all of the messages ahead of time and store them locally on it in the background.

### GET /api/timeline : List TimelineMessage

Updates the timeline cache and returns the new timeline messages since the last update.

# Types

The following types are used in various places in the API.

## Identity

```
{ display_name : String
, bio : String
}
```

## InboxMessage

```
{ id : InboxMessageID
, origin_id : Maybe InboxMessageID
, sender : BladeURL
, sent_datetime : DateTime
, type : String
, content : String
}
```

## OutboxMessage

The `id` and `publish_datetime` fields are only used in `GET` requests.

```
{ id : MessageID
, sent_datetime : DateTime
, receiver : BladeID
, type : PrivateMessageType
, content : Content
}
```

## FeedOptions

```
{ last_seen : Maybe FeedMessageID
}
```

## FeedMessage

The `id` and `publish_datetime` fields are only used in `GET` requests.

```
{ id : FeedMessageID
, publish_datetime : DateTime
, type : FeedMessageType
, content : Content
, permissions_categories : [String]
}
```

## SubscriptionID

```
UrlSafeBase64EncodedPublicSigningKey
```

## Subscription

The `id`, `public_signing_key`, and `last_seen` fields are only used for get requests.

```
{ id : SubscriptionID
, url : URL
, public_signing_key : PublicSigningKey
, last_seen : Maybe FeedMessageID
}
```

## PermissionsGroup

The `id` field is only used for get requests.

```
{ id : PermissionsGroupID
, name : String
, description : String
, members : List BladeID
, permissions : List Permission
}
```

## PermissionsGroupSummary

```
{ id : PermissionsGroupID
, name : String
, description : String
, member_count : Nat
}
```

## PermissionsBladeID

```
UrlSafeBase65EncodedPublicSigningKey
```

## PermissionsBlade

```
List Permission
```

## PermissionsBladeSummary

```
{ id : PermissionsBladeID
, public_signing_key : PublicSigningKey
, permissions : PermissionsBlade
}
```

## TimelineMessage

```
{ id : TimelineMessageID
, retrieve_datetime : DateTime
, url : URL
, origin_id : FeedMessageID
, public_signing_key : PublicSigningKey
, origin_id : FeedMessageID
, publish_datetime : DateTime
, type : FeedMessageType
, content : Content
}
```
