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

from celery.registry import tasks
from requests_oauthlib import OAuth1

from mediagoblin.federation.tools import extract_users, discover_recipient

# Setup logger
_log = logging.getLogger(__name__)
logging.basicConfig()
_log.setLevel(logging.DEBUG)

@celery.task()
def federate_activity(request, activity):
    """
    This federates an activity.

    The activity will need to be serialized so it's sendable across the network
    and then we need to iterate over all the recipients and follow these steps:

    1. Discovery: Lookup the URLs of the user so that we know where to send it
    2. Authorization: Use OAuth 1.0 client authentication to authenticate
    3. Send it to their inbox
    
    The `request` param only needs to be a valid request in order to form a URL
    for the serialization to occur, it won't be used for anything else.
    """
    # First thing to do is serialize the activity we want to send.
    serialized_activity = activity.sanitized_serialize(request)

    # Build up a list of all the recipients we need to send it to.
    # importantly we don't want to send it to the same person twice which
    # so build up a set of all Users to send it to (expand collections to
    # expose each user).
    recipients = set()

    if activity.to:
        recipients = recipients | extract_users(activity.get_to())
    if activity.cc:
        recipients = recipients | extract_users(activity.get_cc())
    if activity.bto:
        recipients = recipients | extract_users(activity.get_bto())
    if activity.bcc:
        recipients = recipients | extract_users(activity.get_bcc())

    # Now iterate over each recipient and send them the activity
    for recipient in recipients:
        # If they're a local user, we can just add it to their own inbox.
        if isinstance(recipient, LocalUser):
            # TODO: Add to local inbox
            pass
        else:
            # Do URL discovery
            # TODO: Caching
            recipients_urls = discover_recipient(recipient)

            # Negotiate OAuth.
            client = pypump.Client(
                webfinger=recipient.webfinger,
                type="web",
            )
            client.register()
            oa = OAuth1(
                client.key,
                client_secret=client.secret
            )
    
            # do POST request to their inbox
            requests = requests.post(
                recipient_urls["activity-inbox"],
                headers={"content-type": "application/json"},
                oauth=oa,
                data=serialized_activity
            )
            import pdb; pdb.set_trace()

    # TODO: store list of recipients it's been distributed to.
