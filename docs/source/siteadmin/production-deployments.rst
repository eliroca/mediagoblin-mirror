.. MediaGoblin Documentation

   Written in 2011, 2012, 2013, 2014, 2015 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

=================================================
Further Considerations for Production Deployments
=================================================

This page extends upon our ":doc:`deploying`" guide to describe some common
issues affecting production deployments.


Should I Keep Open Registration Enabled?
----------------------------------------

Unfortunately, in this current release of MediaGoblin we are suffering
from spammers registering to public instances en masse.  As such, you
may want to either:

a) Disable registration on your instance and just make
   accounts for people you know and trust (eg via the `gmg adduser`
   command).  You can disable registration in your mediagoblin.ini
   like so::

     [mediagoblin]
     allow_registration = false

b) Enable a CAPTCHA plugin.  But unfortunately, though some CAPTCHA
   plugins exist, for various reasons we do not have any general
   recommendations we can make at this point.

We hope to have a better solution to this situation shortly.  We
apologize for the inconvenience in the meanwhile.


Confidential Files
------------------

.. warning::

   The directory ``user_dev/crypto/`` contains confidential information. In
   particular, the ``itsdangeroussecret.bin`` is important for the security of
   login sessions. Make sure not to publish its contents anywhere. If the
   contents gets leaked nevertheless, delete your file and restart the server,
   so that it creates a new secret key. All previous login sessions will be
   invalidated.


.. _background-media-processing:

Background Media Processing
---------------------------

":doc:`deploying`" covers use of a separate Celery process, but this sections
describes this in more detail.

MediaGoblin uses `Celery`_ to handle heavy and long-running tasks. Celery can
be launched in two ways:

1. **Embedded in the main MediaGoblin web application.** This is the way
   ``./lazyserver.sh`` does it for you. It's simple as you only have to run one
   process. The only bad thing with this is that the heavy and long-running
   tasks will run *in* the webserver, keeping the user waiting each time some
   heavy lifting is needed as in for example processing a video. This could lead
   to problems as an aborted connection will halt any processing and since most
   front-end web servers *will* terminate your connection if it doesn't get any
   response from the MediaGoblin web application in a while. This approach is
   suitable for development, small sites or when primarily using :doc:`command
   line uploads <commandline-upload>`.

2. **As a separate web application and media processing application
   (recommended).** In this approach, the MediaGoblin web application delegates
   all media processing to a task queue via a `broker`_ (task queue). This is
   the approach used in our :doc:`deployment guide <deploying>`, with RabbitMQ
   as the broker. This offloads the heavy lifting from the MediaGoblin web
   application and users will be able to continue to browse the site while the
   media is being processed in the background. This approach provided the best
   user experience and is recommended for production sites.

The choice between these two behaviours is controlled by the
``CELERY_ALWAYS_EAGER`` environment variable. Specifying ``true`` instructs
MediaGoblin to processing media within the web application while you wait.
Specifying ``false`` instructs MediaGoblin to use background processing.

.. _`broker`: http://docs.celeryproject.org/en/latest/getting-started/brokers/
.. _`celery`: http://www.celeryproject.org/


.. _sentry:


Error Monitoring with Sentry
----------------------------

We have a plugin for `raven`_ integration, see the ":doc:`/plugindocs/raven`"
documentation.

.. _`raven`: http://raven.readthedocs.org


.. TODO insert init script here
.. TODO are additional concerns ?
   .. Other Concerns
   .. --------------
