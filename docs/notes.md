# Notes for the design of Labrys

## Push and Pull

The ActivityPub model of having inboxes and outboxes is kind of interesting and probably worth copying to some degree. Outboxes would be feeds with pulled updates, inboxes would be pushed updates, notifications, etc. Pushing to an inbox would need to be controlled via the various access control mechanisms that Labrys is intended to encapsulate.

## Follow Requests/etc

One issue when doing something through a decentralized mechanism is how to allow follow requests, direct messages from new people, and other kinds of interactions which could be abused for spam purposes. The general approach that Labrys should probably take is to have policies for deciding whether or not to allow a particular kind of activity, with default policies that are overriden based on the kind of activity.

Here are some plausible policies:

- Friend^n of a Friend: If I follow someone who follows someone who ... follows the person requesting to interact, then it's permissible. The depth of the search can be selected, and the FOAF calculation can in principle be cached periodically to make it not require too much activity every time a request comes in.
- Polling: You could do a poll of folx you know (perhaps a random sampling?) to see if they have reason to distrust a person or advise against following them. The results of these polls could even be used as a kind of reputation system as people "review" more and more people, keeping this info in a feed that you can then review pull automatically. Who you poll and when could be determined by FOAF to some depth.
- FOAF but with ontology: You could also layer onto the FOAF algorithm some kind of ontology of classification system of people. You might follow people for different reasons, eg. some are Friends while others are Enemies To Watch, and you don't necessarily want to let someone message you if they're only ever followed by your enemies. This becomes tricky tho because your friends might similarly be following someone who is an Enemy To Watch, and the notion of trust etc. is complicated. This is a good place to overlay a reputation system.
