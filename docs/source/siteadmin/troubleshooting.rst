.. MediaGoblin Documentation

   Written in 2011, 2012, 2013, 2020, 2021 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _troubleshooting-chapter:

===============
Troubleshooting
===============

Sometimes it doesn't all go to plan! This page describes some of the problems
that community members have reported and how to fix them.


TypeError: object() takes no parameters
---------------------------------------

Backtrace::

    2021-04-04 06:04:55,244 WARNING [mediagoblin.processing] No idea what happened here, but it failed: TypeError('object() takes no parameters',)
    2021-04-04 06:04:55,262 ERROR   [waitress] Exception while serving /submit/
    ...
    File "/opt/mediagoblin/mediagoblin/media_types/video/transcoders.py", line 338, in __setup_videoscale_capsfilter
        caps_struct.set_value('pixel-aspect-ratio', Gst.Fraction(1, 1))
    TypeError: object() takes no parameters

This is caused by not having the package python3-gst-1.0 on Debian:

http://gstreamer-devel.966125.n4.nabble.com/How-to-use-Gst-Fraction-in-python-td4679228.html


alembic.util.exc.CommandError: Can't locate revision identified by 'e9212d3a12d3'
---------------------------------------------------------------------------------

This is caused when you've enabled a plugin, run dbupdate and then disabled the
plugin again. Currently we recommend reinstalling the plugin, but we understand
this is not ideal. See the outstanding issue raised here:

https://issues.mediagoblin.org/ticket/5447

It's possible that manually manipulating the ``alembic_version`` table may help
you, but that approach is only recommended for experienced developers.
