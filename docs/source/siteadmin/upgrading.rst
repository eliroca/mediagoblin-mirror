.. MediaGoblin Documentation

   Written in 2020 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

======================
 Upgrading MediaGoblin
======================

Preparation
-----------

*ALWAYS* take a backup before upgrading, especially before running migrations. That
way if something goes wrong, we can fix things.

Although not strictly necessary, we recommend you shut down your current
MediaGoblin/Celery processes before upgrading.


Upgrade
-------

1. Update to the latest release.  In your ``mediagoblin`` directory, run::

     git fetch && git checkout -q v0.12.0 && git submodule update

2. Note down any plugins you have installed by reviewing your
   ``mediagoblin.ini`` configuration. These will be removed by the following
   steps and must be re-installed.

3. Remove your existing installation::

     make distclean

4. Recreate the virtual environment and install MediaGoblin::

     ./bootstrap.sh && VIRTUALENV_FLAGS='--system-site-packages' ./configure &&
     make

5. Re-install any ":doc:`plugins`" you had previously installed. Skipping these
   may result in errors updating the database.

6. Update the database::

     ./bin/gmg dbupdate

7. Restart the Paster and Celery processes. If you followed ":doc:`deploying`",
   this may be something like::

     sudo systemctl restart mediagoblin-paster.service
     sudo systemctl start mediagoblin-celeryd.service

   To see the logs for troubleshooting, use something like::

     sudo journalctl -u mediagoblin-paster.service -f
     sudo journalctl -u mediagoblin-celeryd.service -f

8. View your site and hover your cursor over the "MediaGoblin" link in the
   footer to confirm the version number you're running.


Updating your system Python
---------------------------

Upgrading your operating system or installing a new major version of Python may
break MediaGoblin. This typically occurs because Python virtual environment is
referring to a copy of Python that no longer exists. In this situation use the
same process for "Upgrade" above.
