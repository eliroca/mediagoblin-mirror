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

import logging

import celery

from mediagoblin.tools.mail import send_email
from mediagoblin.db.models import Notification


_log = logging.getLogger(__name__)


@celery.shared_task()
def email_notification_task(notification_id, message):
    """Celery notification task.

    This task is executed by celeryd to offload long-running operations from
    the web server.
    """
    cn = Notification.query.filter_by(id=notification_id).first()
    _log.info(f'Sending notification email about {cn}')

    return send_email(
        message['from'],
        [message['to']],
        message['subject'],
        message['body'])
