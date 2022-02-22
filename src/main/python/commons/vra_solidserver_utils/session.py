"""
vra_solidserver_utils.session
~~~~~~~~~~~~~~~~

EfficientIP SOLIDserver Requests Session handler

:copyright: (c) 2021 by Julia Leblond.
:license: CeCILL 2.1, see LICENSE for more details.
"""

from requests.sessions import Session
from .auth import SOLIDserverAuth
from urllib.parse import urljoin

class SOLIDserverSession(Session):
	VERBS = ['POST', 'PUT', 'GET', 'DELETE', 'OPTIONS']
	RPC_SERVICES = ['ip_find_free_address']

	def __init__(self, hostname, login, password, cert):
		super(SOLIDserverSession, self).__init__()
		self.base_url = 'https://' + hostname
		self.headers = {'content-type': 'application/json', 'cache-control': 'no-cache'}
		self.verify = cert
		self._auth(login, password)

	def _auth(self, login, password):
		self.auth = SOLIDserverAuth(login, password)

	def request(self, method, service, *args, **kwargs):
		url = urljoin(self.base_url, service)
		return super(SOLIDserverSession, self).request(method, url, *args, **kwargs)
