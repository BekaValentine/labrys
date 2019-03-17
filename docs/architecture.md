# Architecture of Labrys

Labrys consists of five main function components with a standard API, the Labrys API.
These five components are of mixed nature, but they are all integral to achieving the
goal of the Labrys Project. A computer which runs Labrys is called a "blade". 

- A webserver for hosting content

- An identity server that can support multiple decentralized authentication protocols,
  starting with IndieAuth

- A standardized minimal online identity (a profile or bio) that can be used to let
  others know who the owner of the Labrys blade is

- A site-wide means of controlling who can view the content of the site (but not who
  can interact with the identity server nor the biographical information)

- A means of subscribing to content that's hosted by a blade, and viewing it from
  one's own blade frontend.

Labrys provides a frontend for each blade, so that the owner of the blade can access
it remotely over the internet. This front end is primarily used for viewing content
that the blade is subscribed to, or granted access to, but it can also be used to
manage some of the content and settings of the blade. Deeper administration must be
done directly on the blade, by usual means of server administration (e.g. physical
connection, ssh, etc.). On the blade, however, Labrys also provides a convenient
admin UI.

