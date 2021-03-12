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


Upgrade (already on Python 3)
-----------------------------

1. Update to the latest release.  In your ``mediagoblin`` directory, run::

     git fetch && git checkout -q v0.11.0 && git submodule update

2. Remove your existing installation::

     make distclean

3. Install MediaGoblin (changed for 0.11.0, see notes section above)::

     ./bootstrap.sh && VIRTUALENV_FLAGS='--system-site-packages' ./configure && make

   (As of 0.11.0, the upgrade instructions have been updated to use
   ``--system-site-package`` option for consistency with the deployment
   instructions. If this approach causes any problems with for you, re-run
   ``make distclean`` and then ``./bootstrap.sh && ./configure && make`` without
   ``--system-site-packages``.)

4. Update the database::

     ./bin/gmg dbupdate

5. Restart the Paster and Celery processes. If you followed ":doc:`deploying`",
   this may be something like::

     sudo systemctl restart mediagoblin-paster.service
     sudo systemctl start mediagoblin-celeryd.service

   To see the logs for troubleshooting, use something like::

     sudo journalctl -u mediagoblin-paster.service -f
     sudo journalctl -u mediagoblin-celeryd.service -f

6. View your site and hover your cursor over "MediaGoblin" to confirm the
   version number you're running.


Upgrading to Python 3
---------------------

Refer to the "Dependences" and "Configure PostgreSQL" sections of
":doc:`deploying`" to install the necessary Python 3 dependencies. Then follow
the instructions for "Upgrade (already on Python 3)" above.


Updating your system Python
---------------------------

Upgrading your operating system or installing a new version of Python may break
MediaGoblin. This typically occurs because Python virtual environment is
referring to a copy of Python that no longer exists. In this situation use the
same process for "Upgrade (already on Python 3)" above.
