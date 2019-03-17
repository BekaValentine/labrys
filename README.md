# Labrys

A toolkit for web autonomy.



# Motivation

The web, as of 2019, is increasingly centralized. Not just in terms of websites and tools
people use, but in terms of services and how people can even have an "independent" online
presence. Even things such as decentralized identity, like OpenID, are typically run via
centralized systems -- logging in with Google or Facebook is not only widely supported,
but it's also just considerably easier to have a Google or Facebook identity rather than
set up your own.

At the same time, greater control is needed by users. Twitter's persistent refusal to
adequately deal with harassment lead to the development of Mastodon, Facebook's desire
to maximize profits has lead to it manipulating users by cleverly controlling what they
see in their feeds in exchange for advertising and political money. Tumblr censors
"female presenting nipples" in order to avoid running afowl of bad legislation written
by sex-worker-phobic assholes.

The aim of Labrys is to make it easy for people to have control of their online selves,
by having easy to install software that can run identity servers, host websites, and
manage access (both who can access your stuff and how you access others stuff), without
corporate or government ability to shut you down, ban you, or otherwise influence your
site, feed, identity, and so forth.



# Design Goals and Design Choices

Labrys ought to be usable by just about anyone who can use a computer. To that end,
there are a few design goals:

- Labrys should be easy to install. The easier the better.

- Labrys should be relatively cheap, and ideally avoid recurring costs.

- Labrys should be dependent on as few external services as possible.

To achieve these goals, we aim for Labrys to be a software suite that's implemented
in languages that are widely available by default on Linux, using FOSS tools, and
should have built in support for running as a TOR Onion Service. This last choice is
especially important to making sure just about anyone can run Labrys, because not
everyone wants or is able to to spend money every month just to run a webserver, but
most ISPs get very upset if you run one from your home computer. Onion Services,
however, can perfectly well run on your home ISP without getting their attention, and
they have the extra benefit of entirely masking your real world identity so that
your Labrys computer can't be used to doxx you. 

The set up we have in mind, in fact, is a Raspberry Pi or similar little computer,
which is just thrown onto a person's home network. We especially aim to have something
that can be used on a Pi Zero W or other similarly cheap computer, because this would
let us provide the OS with Labrys pre-installed and already set up.



# Why "Labrys"?

A labrys is a two-edged axe. It has many fun associations:

1. Being an axe, a labrys can be used to hack things! Or hack them to pieces! For instance,
   a misbehaving computer, harassers, or capitalism!

2. The word "labrys" is evocative of the word "labyrinth", especially when spoken, and the
   labrys project makes extensive use of TOR's labyrinthine connections to hide labrys
   servers and protect the privacy of the people running them.

3. The labrys is a traditional symbol of lesbianism.
