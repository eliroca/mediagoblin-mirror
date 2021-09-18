# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from celery import current_app


def parser_setup(subparser):
    # No arguments as celery is configured through mediagoblin.ini and
    # paste.ini.
    pass


def celery(args):
    os.environ['CELERY_CONFIG_MODULE'] = 'mediagoblin.init.celery.from_celery'
    from mediagoblin.init.celery.from_celery import setup_self

    # We run setup_self() to initialise Celery with its queue config and set of
    # tasks. That doesn't return anything, so we pick up the configured celery
    # via current_app (kinda scary to manage state like this but oh well).
    setup_self()
    worker = current_app.Worker()
    worker.start()
