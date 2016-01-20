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

import requests

from mediagoblin.db.models import Collection, RemoteUser

def extract_users(audiance_list, ignore=None):
    """ Takes a list (the audiance) and extracts all the users. """
    if ignore is None:
        ignore = []

    # Create the set of users to return
    users = set()

    # Iterate thrugh the audiance
    for audiance in audiance_list:
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
        host_meta = request.get(
            "{0}/.well-know/host-meta".format(base_url),
            headers=headers
        )
    except request.exceptions.RequestException:
        return None

    # If we get anything but a correct response, just bail out.
    if host_meta.status_code != 200:
        return None

    host_meta = host_meta.json()
    return host_meta["links"]
     

def discover_recipient(recipient):
    # Sanity check that we got the remote user
    if not isinstance(recipient, RemoteUser):
        raise Exception("Can only perform discovery on remote users")

    # base URL of site.
    base_url = recipient.webfinger.split("@", 1)[1]
    host_meta = get_host_meta(base_url)

    user_lookup_url = None
    for link in host_meta:
        # It's got to be an lrdd link
        if link["rel"] != "lrdd":
            continue
   
        # The type must be application/json
        if link["type"] != "application/json":
            continue

        # Finally it has to have a template
        if "template" not in link:
            continue

        user_lookup_url = link["template"]

    # Fill in the webfinger into lookup url
    try:
        user_lookup_url = user_lookup_url.format(uri=recipient.webfinger)
    except ValueError:
        # I guess it's invalid somehow?
        return None

    # Request the URLs for this user
    user_urls = request.get(user_lookup_url)

    # If it's anything but a valid request just bail.
    if user_urls.status_code != 200:
        return None

    try:
        user_urls = user_urls.json()
    except Exception:
        return None

    # Okay now just format them into a more usable python dictionary
    links = {}

    for link in user_urls["links"]:
        links[link["rel"]] = link["href"]

    return links
