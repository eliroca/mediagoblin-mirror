=================
Release Checklist
=================

- update docs/sources/siteadmin/relnotes.txt
- update docs/sources/siteadmin/upgrading.txt
- write a blog post
- update mediagoblin/_version.py
- update configure.ac version
- test the upgrade process
- build the docs and check they look good
- git tag v0.11.0 --signed
- push tags
- log in and rebuild master and new version docs on readthedocs.org
- merge into stable branch?
- update mediagoblin/_version.py again to add ".dev" suffix
- update configure.ac version again to add ".dev" suffix

Do we even need a stable branch? I'm not entirely happy with the upgrade
instructions "git fetch && git checkout -q v0.11.0 && git submodule update". Why
have a stable branch if you're asking them to checkout a particular tag anyway?

What to do if you've pushed a tag and the docs need updating?
