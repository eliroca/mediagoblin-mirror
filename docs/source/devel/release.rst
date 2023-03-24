=================
Release Checklist
=================

- update docs/sources/siteadmin/relnotes.txt
- update docs/sources/siteadmin/upgrading.txt
- write a blog post
- test the upgrade process
- build the docs and check they look good
- git tag --annotate v0.11.0 --signed --message
- push tags
- log in and rebuild master and new version docs on readthedocs.org
- merge into stable branch?
- post to mediagoblin-devel
- post to info-gnu@gnu.org
- post to mastodon and twitter
- update IRC topic
- email personal contacts

- update mediagoblin/_version.py
- update configure.ac version
- update mediagoblin/_version.py again to add ".dev" suffix
- update configure.ac version again to add ".dev" suffix

Do we even need a stable branch? I'm not entirely happy with the upgrade
instructions "git fetch && git checkout -q v0.11.0 && git submodule update". Why
have a stable branch if you're asking them to checkout a particular tag anyway?

What to do if you've pushed a tag and the docs need updating?
