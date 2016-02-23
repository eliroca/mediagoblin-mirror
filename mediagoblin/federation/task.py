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
import requests

from requests_oauthlib import OAuth1

from mediagoblin.db.models import Activity, RemoteUser, LocalUser, Collection
from mediagoblin.federation.tools import extract_users, discover_recipient, \
                                         client_registration, FakeRequest

# Setup logger
_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

@celery.task()
def federate_activity(url, activity):
    """
    Federate an activity to it's recipients.

    This takes the request so that we can use it to build the URLs in the
    serialization process and the activity to federate. This task will:

    1. Build up a set of all the recipients in the audience targetting
       fields. This includes expanding collections and creating a set.

    2. Iterate through the recipients and federate it out to each user.
    """
    _log.info("Federating activity id={0}".format(activity))

    # Create the request to use, this is used to generate URLs in serialize
    request = FakeRequest(url)

    # Lookup the activity from the database
    activity = Activity.query.get(activity)

    # First thing to do is serialize the activity we want to send.
    serialized_activity = activity.sanitized_serialize(request)

    # Build up a list of all the recipients we need to send it to.
    # importantly we don't want to send it to the same person twice which
    # so build up a set of all Users to send it to (expand collections to
    # expose each user).
    recipients = set()

    if activity.to:
        recipients = recipients | extract_users(activity.get_to)
    if activity.cc:
        recipients = recipients | extract_users(activity.get_cc)
    if activity.bto:
        recipients = recipients | extract_users(activity.get_bto)
    if activity.bcc:
        recipients = recipients | extract_users(activity.get_bcc)

    # Check there are actually recipients otherwise we can bail out.
    if not recipients:
        return

    # Create a collection to keep track of who has been sent this activity
    recipient_collection = Collection()
    recipient_collection.type = Activity.AUDIENCE_TARGETTING_COLLECTION_TYPE
    recipient_collection.title = "Recipients of Activity {0}".format(activity)
    recipient_collection.save()

    # Now iterate over each recipient and send them the activity
    for recipient in recipients:
        # If they're a local user, we can just add it to their own inbox.
        if isinstance(recipient, LocalUser):
            _log.debug("Federating activity {0} to {1} (local)".format(
                activity.id,
                recipient.username
            ))
            recipient.add_to_inbox(activity)
        else:
            # Dispatch the task to federate it to a remote server.
            federate_remote_user(
                url,
                activity=serialized_activity,
                sender=activity.get_actor,
                recipient=recipient,
                collection=recipient_collection.id
            )

    # We need to add the activity to the senders inbox too.
    activity.get_actor.add_to_inbox(activity)

@celery.task()
def federate_remote_user(url, activity, sender, recipient, collection):
    """
    Federates an activity to a recipient on a remote server.

    This takes a request object, the activity to be federated and the recipient
    which should be a RemoteUser instance and sends it remotely. To do this the
    following steps need to occur:

    1. URL Discovery
    The pump.io uses an approach which means the URLs aren't fixed, they not
    only could be different from what the pump.io software uses right now but
    they could be on different servers entirely. This means we have to look
    those up, we use their webfinger to lookup the /.well-known/host-meta
    defined in Web Host Meta[RFC6415] specification.

    [RFC6415] https://tools.ietf.org/html/rfc6415

    2. Authorization
    The authorization is needed to make requests to the endpoints, the

    3. POST to the Inbox collection
    The activity in full (with bto and bcc fields removed) is then sent to the
    recipient by making a HTTP POST request. This is to a URL endpoint
    discovered in step one (URL Discovery) and containing the Authorization in
    step two. The body is the Activity Streams 1.0 activity serialized to JSON.
    The server then should give us a 200 response to signify the request was
    valid.
    """
    _log.info("Distributing activity {0} to remote user {1}".format(
        activity["id"],
        recipient
    ))

    # Verify the recipient is a RemoteUser
    if not isinstance(recipient, RemoteUser):
        raise ValueError("'recipient' must be a instance of RemoteUser")

    raise Exception(str(activity))

    recipients_urls = discover_recipient(recipient)

    # Register or fetch a client (from database if one exists).
    client = client_registration(
        url.split(":", 1)[1][2:],
        endpoint=recipients_urls["host-meta"]["registration_endpoint"]["href"],
        sender=sender,
        recipient=recipient.webfinger
    )

    # Create the request's OAuth 1.0 authenticator
    oauth = OAuth1(
        client_key=client.id,
        client_secret=client.secret
    )

    # do POST request to their inbox
    response = requests.post(
        recipients_urls["user"]["activity-inbox"]["href"],
        headers={"Content-Type": "application/json"},
        auth=oauth,
        json=activity
    )


    # Check that we got a 200 from the server.
    if response.status_code != 200:
        raise Exception("Server responded with {0} ({1})".format(
            response.content,
            response.status_code
        ))

    # Okay lests add the user to the collection
    recipient_collection = Collection.query.get(collection)
    recipient_collection.add_to_collection(recipient)
