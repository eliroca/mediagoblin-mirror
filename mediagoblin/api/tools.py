def audience_to_object(request, audience):
    """ Converts dictionary to database object from an audience.

    An audience will be either a Collection of people (lists) or a specific
    user, either local or remote.
    """
    # Imported here to prevent cyclic imports.
    from mediagoblin.db.models import LocalUser, RemoteUser

    if "objectType" not in audience:
        return None, "'objectType' properity is missing from audience"

    if audience["objectType"] == "person":
        # For some odd reason sometimes there a phoney "person" pump.io invents
        # and the pump server will add this phoney person to the audience, not
        # sure why but for not just ignore it. This should be investigated!!!
        if "@" not in audience["id"]:
            return None, None

        # Split the ID into the constituent parts.
        username, host = audience["id"][5:].split("@", 1)

        # Is it local or remote.
        if request.host == host:
            user = LocalUser.query.filter_by(username=username).first()
            if user is None:
                return None, "User '{0}' is not known.".format(username)
        else:
            webfinger = "{0}@{1}".format(username, host)
            user = RemoteUser.query.filter_by(webfinger=webfinger).first()

            if user is None:
                user = RemoteUser()
                user.webfinger = webfinger
                user.name = getattr(audience, "displayName")
                user.url = getattr(audience, "url")
                user.bio = getattr(audience, "summary")
                user.save()

        return user, None

    elif audience["objectType"] == "collection":
        raise Exception("Not implemented yet.")
    else:
        return None, "Audience type '{0}' is not known".format(audience["objectType"])
