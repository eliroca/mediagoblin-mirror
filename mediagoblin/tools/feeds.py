# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2021 MediaGoblin contributors.  See AUTHORS.
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

from feedgenerator.django.utils import feedgenerator


class AtomFeedWithLinks(feedgenerator.Atom1Feed):
    """Custom AtomFeed that adds additional top-level links.

    This is used in MediaGoblin for adding pubsubhubub "hub" links to the feed
    via the "push_urls" config. We're porting the feed across to feedgenerator
    due to deprecation of werkzeug.contrib.atom.AtomFeed, so while I've never
    seen this feature in use, but this class allows us to continue to support
    it.

    """
    def __init__(self, *args, links=None, **kwargs):
        super().__init__(*args, **kwargs)
        links = [] if links is None else links
        self.links = links

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        for link in self.links:
            handler.addQuickElement('link', '', link)
