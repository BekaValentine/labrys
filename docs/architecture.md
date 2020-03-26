# Architecture of Labrys

Labrys consists of five main function components with a standard API, the Labrys API. These five components are of mixed nature, but they are all integral to achieving the goal of the Labrys Project. A computer which runs Labrys is called a "blade".

- A webserver for hosting content

- An IndieAuth identity server

- A standardized minimal online identity (a profile or bio) that can be used to let others know who the owner of the Labrys blade is

- A site-wide means of controlling who can view the content of the site (but not who can interact with the identity server nor the biographical information)

- A means of subscribing to content that's hosted by a blade, and viewing it from one's own blade frontend.

Labrys provides a frontend for each blade, so that the owner of the blade can access it remotely over the internet. This front end is primarily used for viewing content that the blade is subscribed to, or granted access to, but it can also be used to manage some of the content and settings of the blade. Deeper administration must be done directly on the blade, by usual means of server administration (e.g. physical connection, ssh, etc.). On the blade, however, Labrys also provides a convenient admin UI.

## Permissions

Every piece of user content on a blade can have access to it restricted. Access privileges work as follows: Any user (i.e. any Blade) can be added to any number of groups. Any piece of user content can have groups and users listed as capable of viewing the content.

Access restrictions are based on the nearest node in the directory structure that has groups defined for it. To understand this, consider first the simplest situation: groups listed for a file specifically. In this situation, the file can only be accessed by members of the listed groups. Consider now a slightly more complicated example, one where the file itself has no permissions, but is inside of a directory that has groups listed. Similarly, this file can only be accessed by people in those listed groups. This proceeds up the directory structure: a file is accessible only by people in the groups listed under the nearest directory with groups defined.

This has the interesting property that permissions are inherited but can be overridden. That is to say, if directory A has group G1 listed, and inside it, another directory, B, lists group G2, then only G2 can access the contents of B. The members of G1 can access the contents of A, excluding B.

### Groups

By default, there are two groups, `ALL` and `NONE`. Every person is in group `ALL`, whereas no one except the Blade owner is in group `NONE`. This means that `ALL` can be seen as meaning "public", while `NONE` can be seen as meaning "my unshared files". Other group names can be defined as well.

### Format of `restricted_user_content` directory

The `restricted_user_content` directory is intended to mirror the structure of `user_content` wherever restrictions need to be placed. Each directory in `user_content` which has restrictions corresponds to a directory in `restricted_user_content`. If the directory itself has restrictions, then the corresponding directory has either a file `groups` listing the groups that can access the directory, or a file `people`, listing the domains of the people that can access the directory, or both. If a file in the directory has restrictions, then the corresponding directory contains a subdirectory named `files` and the file has a corresponding permissions file with the same name but with `.groups` or `.people` appended to the end. Similarly, if a anything within a subdirectory has restrictions, then the corresponding directory contains a subdirectory called `directories` with recursive structure.

So for example suppose `user_content` has the following structure and restrictions:

```
user_content/
├── public/ : this is public data for anyone to view
│   └── a.txt
└── private/ : this is all private and no one but me can view it
    ├── b.jpg
    ├── c.mp3 : except this, which can be viewed by anyone in group C
    └── d.avi : and this, which can be viewed by the owner of cool.site.net
```

The `restricted_user_content` directory would therefore have the following structure and content:

```
restricted_user_content/
└── directories/
    └── private/
        ├── groups : contents = "NONE"
        └── files/
            ├── c.mp3.groups : contents = "C"
            └── d.avi.people : contents = "cool.site.net"
```

## Blade Backend Structure

The Blade backend is a flat file system organized as follows:

```
LABRYS_ROOT/
├── README.md
├── LICENSE.md
├── docs/ : contains documentation about Labrys
└── dev/ : contains the primary code and relevant data to run the blade
    ├── setup.py : the setup script
    ├── blade.py : the blade server
    ├── src/ : additional python files
    ├── templates/ : html templates
    └── data/ : holds all of the backend data
        ├── blade_url.txt : contains the canonical URL of this blade
        ├── session_secret_key.txt : holds the secret key to use for session management
        ├── authentication/ : holds data pertaining to authenticating the blade user
        │   ├── password_hash.txt : bcrypt hash of the user's password + salt
        │   ├── auth_state/ : auth states
        │   └── auth_tokens/ : auth tokens
        │   ├── identity/ : holds the data pertaining to the Blade owner's public identity use for viewing followers etc.
        │   │   ├── avatar.{png,jpg,gif} : the Blade owner's avatar
        │   │   ├── bio.txt : the Blade owner's bio, short self description, etc.
        │   │   ├── display_name.txt : the Blade owner's display name
        │   │   ├── private_signing_key.txt : the private portion of the signing key used to identify this blade
        │   │   └── public_signing_key.txt : the public portion of the signing key used to identify this blade
        │   └── permissions/ : specifies permissions for feeds
        ...
```
