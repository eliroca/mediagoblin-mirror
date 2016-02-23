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

from requests.utils import to_native_string
from oauthlib.oauth1 import Client, SIGNATURE_HMAC

class PumpOAuth(object):
	def __init__(self, key, secret):
		self.key = key
		self.secret = secret
		
		self.client = Client(
			self.key,
			self.secret,
			signature_method=SIGNATURE_HMAC,
		)
	
	def __call__(self, request):
		request.url, headers, request.body = self.client.sign(
			unicode(request.url),
			unicode(request.method),
			request.body,
			request.headers
		)
		
		request.prepare_headers(headers)
		request.url = to_native_string(request.url)
		return request
		