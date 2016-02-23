# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2014 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.db.models import Activity, Generator, User, LocalUser, \
                                  RemoteUser

def create_generator(request):
    """
    This creates a Generator object based on the Client associated with the
    OAuth credentials used. If the request has invalid OAuth credentials or
    no OAuth credentials None is returned.
    """
    if not hasattr(request, "access_token"):
        return None

    client = request.access_token.get_requesttoken.get_client

    # Check if there is a generator already
    generator = Generator.query.filter_by(
        name=client.application_name,
        object_type="client"
    ).first()
    if generator is None:
        generator = Generator(
            name=client.application_name,
            object_type="client"
        )
        generator.save()

    return generator

def audience_to_users(audience):
    """ Covnerts comma seperated list of people to list of User objects """
    if not audience:
        return []

    audience = audience.replace(" ", "").split(",")
    users = []
    for person in audience:
        # Is it a remote user (i.e. webfinger)
        if "@" in person:
            user = RemoteUser.query.filter_by(webfinger=person).first()
            if user is None:
                user = RemoteUser()
                user.webfinger = person
                user.save()
        else:
            user = LocalUser.query.filter_by(username=person).first()

        if user is None:
            continue # skip, it's probably a typo or collection

        users.append(user)

    return users

def create_activity(verb, obj, actor, target=None, generator=None,
                    to=None, cc=None):
    """
    This will create an Activity object which for the obj if possible
    and save it. The verb should be one of the following:
        add, author, create, delete, dislike, favorite, follow
        like, post, share, unfollow, unfavorite, unlike, unshare,
        update, tag.

    If none of those fit you might not want/need to create an activity for
    the object. The list is in mediagoblin.db.models.Activity.VALID_VERBS
    """
    # exception when we try and generate an activity with an unknow verb
    # could change later to allow arbitrary verbs but at the moment we'll play
    # it safe.

    if verb not in Activity.VALID_VERBS:
        raise ValueError("A invalid verb type has been supplied.")

    if generator is None:
        # This should exist as we're creating it by the migration for Generator
        generator = Generator.query.filter_by(name="GNU MediaGoblin").first()
        if generator is None:
            generator = Generator(
                name="GNU MediaGoblin",
                object_type="service"
            )
            generator.save()

    # Ensure the object has an ID which is needed by the activity.
    obj.save(commit=False)

    # Create the activity
    activity = Activity(verb=verb)
    activity.object = obj

    if target is not None:
        activity.target = target

   # If they've set it override the actor from the obj.
    activity.actor = actor.id if isinstance(actor, User) else actor
    activity.generator = generator.id
    activity.save()

    # Split the to and cc fields from comma seperated strings to User's
    to = audience_to_users(to)
    cc = audience_to_users(cc)

    # Add the audience
    activity.add_to_audience(*to)
    activity.add_cc_audience(*cc)

    # Sigh want to do this prior to save but I can't figure a way to get
    # around relationship() not looking up object when model isn't saved.
    if activity.generate_content():
        activity.save()

    return activity
