from __future__ import absolute_import
from dialback import DialbackEndpoint

class GMGDialbackEndpoint(DialbackEndpoint):

    def validate_unique(self, id, url, token, date):
        # TODO: Verify this properly to prevent reply attacks
        return True
