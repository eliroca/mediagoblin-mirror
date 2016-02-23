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
import json
import requests
import dialback

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import BaseRequest

from mediagoblin.db.models import Client, Collection, User
from mediagoblin.routing import get_url_map

class FakeRequest(BaseRequest):
    """
    This emulates a request for the purposes to pass it into serialize and
    unserialize functions. It takes in the base URL (e.g. the URL with scheme)
    but no path and then it will provide a "request" that you can pass in. This
    will provide you with the request.urlgen function for building external (or
    internal) URLs

    Example usage:
    >>> from mediagoblin.federation.tools import FakeRequest
    >>> request = FakeRequest("https://my.mediagoblin.org")
    """

    def __init__(self, url):
        self.base_url = url.split("://", 1)[1]

        url_map = get_url_map()
        request_builder = EnvironBuilder(base_url=url)

        # Get the Environ, and get the URL mapper.
        self.environ = request_builder.get_environ()
        self.mapper = url_map.bind_to_environ(self.environ)

    def urlgen(self, endpoint, **kw):
        try:
            qualified = kw.pop('qualified')
        except KeyError:
            qualified = False

        return self.mapper.build(
            endpoint,
            values=dict(**kw),
            force_external=qualified
        )

def client_registration(server_host, endpoint, sender, recipient, timeout=10):
    """ Registers the client or fetches stored credentials """
    # Split the recipient's webfinger so we can get the host and username.
    username, host = recipient.split("@", 1)

    # Check the database and check if we have any.
    try:
        return Client.query.get(
            user=sender.id,
            host=host
        )
    except Exception:
        # I guess we're going to have to create one ourselves.
        pass

    # Split the recipient's webfinger so we can get the host and username.
    username, host = recipient.split("@", 1)
    context = {
        "type": "client_associate",
        "application_type": "web",
        "application_name": "GNU Mediagoblin",
    }

    # Make the dialback client for this request
    sender_webfinger = sender.get_public_id(server_host)[5:]
    dialback_auth = dialback.DialbackAuth(webfinger=sender_webfinger)

    # Make the request for client credentials.
    response = requests.post(
        endpoint,
        headers={"Content-Type": "application/json"},
        data=json.dumps(context),
        auth=dialback_auth
    )

    # Check we got a 200
    if response.status_code != 200:
        # TODO: Convert this to a mediagoblin specifc exception.
        raise Exception("Could not register client for activity federation.")

    # Get the JSON response
    response_data = response.json()

    # Verify we have the required fields in our response.
    assert "client_id" in response_data
    assert "client_secret" in response_data

    # Save the client
    client = Client(
        id=response_data["client_id"],
        secret=response_data["client_secret"],
        user=sender.id,
        host=host,
        application_type=context["application_type"]
    )
    client.save()

    # Return the client ID and secret pair
    return client

def extract_users(audiance_list, ignore=None):
    """ Takes a list (the audiance) and extracts all the users. """
    if ignore is None:
        ignore = []

    # Create the set of users to return
    users = set()

    # Iterate through the audiance
    for audiance_ci in audiance_list.get_collection_items():
        # Extract the object from the CollectionItem
        audiance = audiance_ci.get_object()

        # If the audiance is on the ignore list, skip past it
        if audiance in ignore:
            continue

        # we found a user, we can just add them straight to the list
        if isinstance(audiance, User):
            users.add(audiance)

        # If we've found a collection, expand it and add them.
        elif isinstance(audiance, Collection):
            collection_audiance = audiance.get_collection_items()

            # Ignore this collection or we might get into a cycle.
            collection_audiance = extract_users(
                collection_audiance,
                (ignore + [audiance])
            )

            users = users | collection_audiance

    return users

def get_host_meta(url):
    """ Gets the host meta data for a URL """
    # Build headers
    headers = {
        "content-type": "application/json",
    }

    # Try and get the host-meta
    try:
        host_meta = requests.get(
            "{0}/.well-known/host-meta".format(url),
            headers=headers
        )
    except requests.exceptions.RequestException:
        return None

    # If we get anything but a correct response, just bail out.
    if host_meta.status_code != 200:
        return None

    host_meta = host_meta.json()
    return host_meta["links"]


def discover_recipient(recipient):
    """
    Discover the URLs for the receipient.

    TODO: This should be in PyPump.
    """
    # base URL of site.
    username, host = recipient.webfinger.split("@", 1)
    host_meta = get_host_meta("http://{0}".format(host))
    assert host_meta != None

    # Create the links block which will contain host-meta and the user's URLs
    links = {}

    # Iterate through the host meta assigning them to the links block.
    hostmeta_links = {}
    for link in host_meta:
        # If for whatever odd reason it doesn't have a "rel" skip it.
        if "rel" not in link:
            continue

        # Get the rel value out (so it's not in the values)
        rel = link.pop("rel")

        # Assign it so the rel is the key and all the other information is there.
        hostmeta_links[rel] = link
    links["host-meta"] = hostmeta_links

    # If for whatever the lrdd lookup isn't there, just return with what we have.
    if "lrdd" not in hostmeta_links:
        return links

    # Extract and populate the template
    user_lookup = hostmeta_links["lrdd"]["template"].format(
        uri=recipient.webfinger
    )

    # Request the URLs for this user
    user_urls = requests.get(user_lookup).json()

    user_links = {}
    for link in user_urls["links"]:
        # Again, if it doesn't have a "rel" just skip.
        if "rel" not in link:
            continue

        # Extract the rel to be used as a key later
        rel = link.pop("rel")

        # Save the link in user_links
        user_links[rel] = link

    links["user"] = user_links
    return links
