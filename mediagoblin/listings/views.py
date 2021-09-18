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

from mediagoblin import mg_globals
from mediagoblin.db.models import MediaEntry
from mediagoblin.db.util import media_entries_for_tag_slug
from mediagoblin.decorators import uses_pagination
from mediagoblin.plugins.api.tools import get_media_file_paths
from mediagoblin.tools.feeds import AtomFeedWithLinks
from mediagoblin.tools.pagination import Pagination
from mediagoblin.tools.response import render_to_response
from mediagoblin.tools.translate import pass_to_ugettext as _

from werkzeug.wrappers import Response


def _get_tag_name_from_entries(media_entries, tag_slug):
    """
    Get a tag name from the first entry by looking it up via its slug.
    """
    # ... this is slightly hacky looking :\
    tag_name = tag_slug

    for entry in media_entries:
        for tag in entry.tags:
            if tag['slug'] == tag_slug:
                tag_name = tag['name']
                break
        break
    return tag_name


@uses_pagination
def tag_listing(request, page):
    """'Gallery'/listing for this tag slug"""
    tag_slug = request.matchdict['tag']

    cursor = media_entries_for_tag_slug(request.db, tag_slug)
    cursor = cursor.order_by(MediaEntry.created.desc())

    pagination = Pagination(page, cursor)
    media_entries = pagination()

    tag_name = _get_tag_name_from_entries(media_entries, tag_slug)

    return render_to_response(
        request,
        'mediagoblin/listings/tag.html',
        {'tag_slug': tag_slug,
         'tag_name': tag_name,
         'media_entries': media_entries,
         'pagination': pagination})


ATOM_DEFAULT_NR_OF_UPDATED_ITEMS = 15


def atom_feed(request):
    """
    generates the atom feed with the tag images
    """
    tag_slug = request.matchdict.get('tag')
    feed_title = "MediaGoblin Feed"
    if tag_slug:
        feed_title += " for tag '%s'" % tag_slug
        link = request.urlgen('mediagoblin.listings.tags_listing',
                              qualified=True, tag=tag_slug)
        cursor = media_entries_for_tag_slug(request.db, tag_slug)
    else:  # all recent item feed
        feed_title += " for all recent items"
        link = request.urlgen('index', qualified=True)
        cursor = MediaEntry.query.filter_by(state='processed')
    cursor = cursor.order_by(MediaEntry.created.desc())
    cursor = cursor.limit(ATOM_DEFAULT_NR_OF_UPDATED_ITEMS)

    """
    ATOM feed id is a tag URI (see http://en.wikipedia.org/wiki/Tag_URI)
    """
    atomlinks = []
    if mg_globals.app_config["push_urls"]:
        for push_url in mg_globals.app_config["push_urls"]:
            atomlinks.append({
                'rel': 'hub',
                'href': push_url})

    feed = AtomFeedWithLinks(
        title=feed_title,
        link=link,
        description='',
        feed_url=request.url,
        links=atomlinks,
    )

    for entry in cursor:
        # Include a thumbnail image in content.
        file_urls = get_media_file_paths(entry.media_files, request.urlgen)
        if 'thumb' in file_urls:
            content = '<img src="{thumb}" alt='' /> {desc}'.format(
                thumb=file_urls['thumb'], desc=entry.description_html)
        else:
            content = entry.description_html

        feed.add_item(
            # AtomFeed requires a non-blank title. This situation can occur if
            # you edit a media item and blank out the existing title.
            title=entry.get('title') or _('Untitled'),
            link=entry.url_for_self(
                request.urlgen,
                qualified=True),
            description=content,
            unique_id=entry.url_for_self(request.urlgen, qualified=True),
            author_name=entry.get_actor.username,
            author_link=request.urlgen(
                    'mediagoblin.user_pages.user_home',
                    qualified=True,
                    user=entry.get_actor.username),
            updateddate=entry.get('created'),
        )

    response = Response(
        feed.writeString(encoding='utf-8'),
        mimetype='application/atom+xml'
    )
    return response
