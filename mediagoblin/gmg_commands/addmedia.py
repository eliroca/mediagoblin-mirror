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

from mediagoblin.db.models import LocalUser
from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.submit.lib import (
    submit_media, FileUploadLimit, UserUploadLimit, UserPastUploadLimit)

from mediagoblin import mg_globals


def parser_setup(subparser):
    subparser.add_argument(
        'username',
        help="Name of user this media entry belongs to")
    subparser.add_argument(
        'filename',
        help="Local file on filesystem")
    subparser.add_argument(
        "-d", "--description",
        help="Description for this media entry")
    subparser.add_argument(
        "-t", "--title",
        help="Title for this media entry")
    subparser.add_argument(
        "-l", "--license",
        help=(
            "License this media entry will be released under. "
            "Should be a URL."))
    subparser.add_argument(
        "-T", "--tags",
        help=(
            "Comma separated list of tags for this media entry."))
    subparser.add_argument(
        "-s", "--slug",
        help=(
            "Slug for this media entry. "
            "Will be autogenerated if unspecified."))
    subparser.add_argument(
        "-c", "--collection-slug",
        help=(
            "Slug of the collection for this media entry. "
            "Should already exist."))

    subparser.add_argument(
        '--celery',
        action='store_true',
        help="Don't process eagerly, pass off to celery")


def addmedia(args):
    # Run eagerly unless explicetly set not to
    if not args.celery:
        os.environ['CELERY_ALWAYS_EAGER'] = 'true'

    app = commands_util.setup_app(args)

    # get the user
    user = app.db.LocalUser.query.filter(
        LocalUser.username==args.username.lower()
    ).first()
    if user is None:
        print("Sorry, no user by username '%s'" % args.username)
        return

    # check for the file, if it exists...
    filename = os.path.split(args.filename)[-1]
    abs_filename = os.path.abspath(args.filename)
    if not os.path.exists(abs_filename):
        print("Can't find a file with filename '%s'" % args.filename)
        return

    def maybe_unicodeify(some_string):
        # this is kinda terrible
        if some_string is None:
            return None
        return some_string

    try:
        submit_media(
            mg_app=app,
            user=user,
            submitted_file=open(abs_filename, 'rb'), filename=filename,
            title=maybe_unicodeify(args.title),
            description=maybe_unicodeify(args.description),
            collection_slug=args.collection_slug,
            license=maybe_unicodeify(args.license),
            tags_string=maybe_unicodeify(args.tags) or "")
    except FileUploadLimit:
        print("This file is larger than the upload limits for this site.")
    except UserUploadLimit:
        print("This file will put this user past their upload limits.")
    except UserPastUploadLimit:
        print("This user is already past their upload limits.")
