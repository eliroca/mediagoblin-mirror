.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _configuration-chapter:

========================
Configuring MediaGoblin
========================

So!  You've got MediaGoblin up and running, but you need to adjust
some configuration parameters.  Well you've come to the right place!


MediaGoblin's config files
==========================

There are two main files used to configure MediaGoblin:

``mediagoblin.ini``
  This is the main config file for MediaGoblin. If you want to tweak any
  settings for MediaGoblin, you'll usually do that here. This file is copied
  from ``mediagoblin.example.ini`` the first time MediaGoblin runs. Keep this in
  mind if you ever need to refer back to the original settings.

``paste.ini``
  This is primarily a server configuration file, on the Python side
  (specifically, on the WSGI side, via `paste deploy
  <http://pythonpaste.org/deploy/>`_ / `paste script
  <http://pythonpaste.org/script/>`_).  It also sets up some
  middleware that you can mostly ignore, except to configure
  sessions... more on that later.  If you are adding a different
  Python server other than Waitress / plain HTTP, you might configure it
  here.  You probably won't need to change this file very much.

Changes to these two files only take effect after restarting MediaGoblin. If you
followed your deployment guide, see the section on :ref:`restarting MediaGoblin
<restarting mediagoblin>`. If you're using ``lazyserver.sh`` or
``lazycelery.sh``, first quit with ``Ctrl-c`` and then re-run the command.

Enabling extra media types or plugins may require an update to the database, so
after making changes, it is also a good idea to run::

  $ ./bin/gmg dbupdate


Common changes
==============

Enabling email notifications
----------------------------

You'll almost certainly want to enable sending email.  By default,
MediaGoblin doesn't really do this... for the sake of developer
convenience, it runs in "email debug mode".

To make MediaGoblin send email, you need a mailer daemon.

Change this in your ``mediagoblin.ini`` file::

    email_debug_mode = false

You should also change the "from" email address by setting
``email_sender_address``. For example::

    email_sender_address = "foo@example.com"

If you have more custom SMTP settings, you also have the following
options at your disposal, which are all optional, and do exactly what
they sound like.

- ``email_smtp_host``
- ``email_smtp_port``
- ``email_smtp_user``
- ``email_smtp_pass``
- ``email_smtp_use_ssl`` (default is ``False``)
- ``email_smtp_force_starttls`` (default is ``False``)


Changing the data directory
---------------------------

MediaGoblin by default stores your data in wherever ``data_basedir``.
This can be changed by changing the value in your ``mediagoblin.ini`` file
for example::

    [DEFAULT]
    data_basedir = "/var/mediagoblin/user_data"

For efficiency reasons MediaGoblin doesn't serve these files itself and
instead leaves that to the webserver. You will have to alter the location
to match the path in ``data_basedir``.

If you use ``lazyserver.sh`` you need to change the ``paste.ini`` file::

    [app:mediagoblin]
    /mgoblin_media = /var/mediagoblin/user_data

If you use Nginx you need to change the config::

     # Instance specific media:
     location /mgoblin_media/ {
         alias /var/mediagoblin/user_data;
     }

Once you have done this you will need to move any existing media you had in the
old directory to the new directory so existing media still can be displayed.


All other configuration changes
-------------------------------

There are a number of other settings which aren't documented here. Currently,
the best reference for these options is ``mediagoblin/config_spec.ini`` and the
additional config specifications for each media type eg.
``mediagoblin/media_types/video/config_spec.ini``. These files are the
specification for ``mediagoblin.ini`` and define the types and default values
for each configuration option.
